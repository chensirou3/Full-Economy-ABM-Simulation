"""
场景管理 API 路由
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any
import yaml
import json
from pathlib import Path
import structlog

from ..dependencies import get_simulation_scheduler
from ...simcore.config import SimulationConfig, load_scenario_config


logger = structlog.get_logger()
router = APIRouter()

# 场景存储目录
SCENARIOS_DIR = Path("scenarios")
SCENARIOS_DIR.mkdir(exist_ok=True)


class ScenarioInfo(BaseModel):
    """场景信息"""
    name: str
    description: str
    file_path: str
    size: int
    modified_time: float


@router.get("/", response_model=List[ScenarioInfo])
async def list_scenarios():
    """列出所有可用场景"""
    scenarios = []
    
    # 扫描场景目录
    for scenario_file in SCENARIOS_DIR.glob("*.yml"):
        try:
            stat = scenario_file.stat()
            
            # 尝试读取场景描述
            with open(scenario_file, 'r', encoding='utf-8') as f:
                scenario_data = yaml.safe_load(f)
                description = scenario_data.get('description', '无描述')
            
            scenarios.append(ScenarioInfo(
                name=scenario_file.stem,
                description=description,
                file_path=str(scenario_file),
                size=stat.st_size,
                modified_time=stat.st_mtime,
            ))
            
        except Exception as e:
            logger.warning("读取场景文件失败", 
                          file=str(scenario_file),
                          error=str(e))
            continue
    
    return scenarios


@router.get("/{scenario_name}")
async def get_scenario(scenario_name: str):
    """获取指定场景的配置"""
    scenario_file = SCENARIOS_DIR / f"{scenario_name}.yml"
    
    if not scenario_file.exists():
        raise HTTPException(status_code=404, detail="场景不存在")
    
    try:
        config = load_scenario_config(scenario_file)
        return {
            "status": "success",
            "data": config.dict(),
        }
    except Exception as e:
        logger.error("加载场景失败", scenario=scenario_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"加载场景失败: {str(e)}")


@router.post("/load/{scenario_name}")
async def load_scenario(scenario_name: str):
    """加载并应用指定场景"""
    scenario_file = SCENARIOS_DIR / f"{scenario_name}.yml"
    
    if not scenario_file.exists():
        raise HTTPException(status_code=404, detail="场景不存在")
    
    try:
        # 加载场景配置
        config = load_scenario_config(scenario_file)
        
        # 获取调度器并重新初始化
        scheduler = get_simulation_scheduler()
        await scheduler.stop()
        await scheduler.initialize(config)
        
        logger.info("场景已加载", scenario=scenario_name)
        
        return {
            "status": "success",
            "message": f"场景 '{scenario_name}' 已加载",
            "config": config.dict(),
        }
        
    except Exception as e:
        logger.error("加载场景失败", scenario=scenario_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"加载场景失败: {str(e)}")


@router.post("/upload")
async def upload_scenario(file: UploadFile = File(...)):
    """上传新场景文件"""
    if not file.filename.endswith(('.yml', '.yaml')):
        raise HTTPException(status_code=400, detail="只支持 YAML 格式的场景文件")
    
    try:
        # 读取文件内容
        content = await file.read()
        scenario_data = yaml.safe_load(content.decode('utf-8'))
        
        # 验证场景配置
        try:
            SimulationConfig(**scenario_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"场景配置无效: {str(e)}")
        
        # 保存文件
        scenario_name = Path(file.filename).stem
        scenario_file = SCENARIOS_DIR / f"{scenario_name}.yml"
        
        with open(scenario_file, 'w', encoding='utf-8') as f:
            yaml.dump(scenario_data, f, default_flow_style=False, allow_unicode=True)
        
        logger.info("场景文件已上传", scenario=scenario_name)
        
        return {
            "status": "success",
            "message": f"场景 '{scenario_name}' 已上传",
            "file_path": str(scenario_file),
        }
        
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML 格式错误: {str(e)}")
    except Exception as e:
        logger.error("上传场景失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.delete("/{scenario_name}")
async def delete_scenario(scenario_name: str):
    """删除指定场景"""
    scenario_file = SCENARIOS_DIR / f"{scenario_name}.yml"
    
    if not scenario_file.exists():
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 不允许删除内置场景
    builtin_scenarios = ["baseline", "credit_boom", "supply_shock"]
    if scenario_name in builtin_scenarios:
        raise HTTPException(status_code=403, detail="不能删除内置场景")
    
    try:
        scenario_file.unlink()
        logger.info("场景已删除", scenario=scenario_name)
        
        return {
            "status": "success",
            "message": f"场景 '{scenario_name}' 已删除",
        }
        
    except Exception as e:
        logger.error("删除场景失败", scenario=scenario_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/validate/{scenario_name}")
async def validate_scenario(scenario_name: str):
    """验证场景配置"""
    scenario_file = SCENARIOS_DIR / f"{scenario_name}.yml"
    
    if not scenario_file.exists():
        raise HTTPException(status_code=404, detail="场景不存在")
    
    try:
        # 尝试加载和验证配置
        config = load_scenario_config(scenario_file)
        
        # 进行额外的一致性检查
        validation_results = []
        
        # 检查人口与地图大小的匹配
        total_area = config.world.grid.rows * config.world.grid.cols * (config.world.grid.cell_km ** 2)
        population_density = config.population.N / total_area
        
        if population_density > 1000:
            validation_results.append({
                "type": "warning",
                "message": f"人口密度过高: {population_density:.1f} 人/km²",
            })
        
        # 检查城市数量与地图大小
        total_cells = config.world.grid.rows * config.world.grid.cols
        if config.world.generator.city_count > total_cells // 100:
            validation_results.append({
                "type": "error",
                "message": "城市数量相对于地图大小过多",
            })
        
        return {
            "status": "success",
            "valid": len([r for r in validation_results if r["type"] == "error"]) == 0,
            "validation_results": validation_results,
            "config": config.dict(),
        }
        
    except Exception as e:
        logger.error("验证场景失败", scenario=scenario_name, error=str(e))
        return {
            "status": "error",
            "valid": False,
            "error": str(e),
        }
