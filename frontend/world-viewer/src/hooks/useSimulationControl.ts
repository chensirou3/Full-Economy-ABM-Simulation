/**
 * 模拟控制 Hook
 * 提供播放、暂停、步进等控制功能
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { simulationApi } from '../api/simulation'
import { useSimulationStore } from '../store/simulationStore'

export const useSimulationControl = () => {
  const queryClient = useQueryClient()
  const { setConnectionError } = useSimulationStore()
  
  const playMutation = useMutation({
    mutationFn: (speed?: number) => simulationApi.play(speed),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation-status'] })
    },
    onError: (error: any) => {
      setConnectionError(error.message || '播放失败')
    },
  })
  
  const pauseMutation = useMutation({
    mutationFn: simulationApi.pause,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation-status'] })
    },
    onError: (error: any) => {
      setConnectionError(error.message || '暂停失败')
    },
  })
  
  const stepMutation = useMutation({
    mutationFn: (steps: number) => simulationApi.step(steps),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation-status'] })
    },
    onError: (error: any) => {
      setConnectionError(error.message || '步进失败')
    },
  })
  
  const speedMutation = useMutation({
    mutationFn: (speed: number) => simulationApi.setSpeed(speed),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation-status'] })
    },
    onError: (error: any) => {
      setConnectionError(error.message || '设置速度失败')
    },
  })
  
  const jumpMutation = useMutation({
    mutationFn: (targetTime: number) => simulationApi.jump(targetTime),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation-status'] })
    },
    onError: (error: any) => {
      setConnectionError(error.message || '时间跳转失败')
    },
  })
  
  const rewindMutation = useMutation({
    mutationFn: (targetTime: number) => simulationApi.rewind(targetTime),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation-status'] })
    },
    onError: (error: any) => {
      setConnectionError(error.message || '倒带失败')
    },
  })
  
  const resetMutation = useMutation({
    mutationFn: simulationApi.reset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation-status'] })
    },
    onError: (error: any) => {
      setConnectionError(error.message || '重置失败')
    },
  })
  
  return {
    play: (speed?: number) => playMutation.mutate(speed),
    pause: () => pauseMutation.mutate(),
    step: (steps: number = 1) => stepMutation.mutate(steps),
    setSpeed: (speed: number) => speedMutation.mutate(speed),
    jump: (targetTime: number) => jumpMutation.mutate(targetTime),
    rewind: (targetTime: number) => rewindMutation.mutate(targetTime),
    reset: () => resetMutation.mutate(),
    
    isLoading: (
      playMutation.isPending ||
      pauseMutation.isPending ||
      stepMutation.isPending ||
      speedMutation.isPending ||
      jumpMutation.isPending ||
      rewindMutation.isPending ||
      resetMutation.isPending
    ),
  }
}
