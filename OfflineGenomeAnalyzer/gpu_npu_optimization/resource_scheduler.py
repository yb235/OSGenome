"""
Advanced Resource Scheduler for Hybrid Computing
Prevents interference between GPU, NPU, and CPU workloads
"""

import os
import time
import threading
import queue
import psutil
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

try:
    import cupy as cp
    CUDA_AVAILABLE = True
except ImportError:
    CUDA_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class ComputeUnit(Enum):
    """Available compute units"""
    CPU = "cpu"
    GPU = "gpu"
    NPU = "npu"


@dataclass
class WorkBatch:
    """Work batch for scheduling"""
    batch_id: str
    data: Any
    priority: int
    compute_unit: ComputeUnit
    estimated_time: float
    memory_requirement: int


@dataclass
class ResourceState:
    """Current state of compute resources"""
    cpu_usage: float
    cpu_available_cores: int
    gpu_usage: float
    gpu_memory_free: int
    npu_usage: float
    system_memory_free: int
    timestamp: float


class ResourceMonitor:
    """Real-time resource monitoring for scheduling decisions"""
    
    def __init__(self, update_interval: float = 0.1):
        self.update_interval = update_interval
        self.monitoring = False
        self.current_state = ResourceState(0, 0, 0, 0, 0, 0, time.time())
        self.monitor_thread = None
        
    def start(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
            
    def _monitor_loop(self):
        """Continuous monitoring loop"""
        while self.monitoring:
            # CPU monitoring
            cpu_usage = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count()
            cpu_available = max(0, cpu_count - int(cpu_count * cpu_usage / 100))
            
            # System memory
            memory = psutil.virtual_memory()
            memory_free = memory.available
            
            # GPU monitoring
            gpu_usage = 0
            gpu_memory_free = 0
            if CUDA_AVAILABLE:
                try:
                    gpu_memory_pool = cp.get_default_memory_pool()
                    gpu_memory_info = cp.cuda.runtime.memGetInfo()
                    gpu_memory_free = gpu_memory_info[0]  # Free memory
                    
                    # Estimate GPU usage based on memory allocation
                    total_gpu_memory = gpu_memory_info[1]
                    used_gpu_memory = total_gpu_memory - gpu_memory_free
                    gpu_usage = (used_gpu_memory / total_gpu_memory) * 100
                except:
                    pass
            
            # NPU monitoring (simplified - actual implementation depends on hardware)
            npu_usage = 0
            if TORCH_AVAILABLE:
                # Estimate NPU usage based on active processes
                # This is simplified - real NPU monitoring requires specific APIs
                if torch.cuda.is_available():
                    gpu_usage = min(100, gpu_usage + 10)  # Approximate overlap
                elif torch.backends.mps.is_available():
                    # Apple Neural Engine monitoring would require specific APIs
                    npu_usage = 20  # Placeholder
            
            # Update current state
            self.current_state = ResourceState(
                cpu_usage=cpu_usage,
                cpu_available_cores=cpu_available,
                gpu_usage=gpu_usage,
                gpu_memory_free=gpu_memory_free,
                npu_usage=npu_usage,
                system_memory_free=memory_free,
                timestamp=time.time()
            )
            
            time.sleep(self.update_interval)
            
    def get_current_state(self) -> ResourceState:
        """Get current resource state"""
        return self.current_state


class IntelligentScheduler:
    """
    Intelligent scheduler that prevents interference between compute units
    Uses resource monitoring and workload analysis for optimal distribution
    """
    
    def __init__(self):
        self.resource_monitor = ResourceMonitor()
        self.work_queues = {
            ComputeUnit.CPU: queue.PriorityQueue(),
            ComputeUnit.GPU: queue.PriorityQueue(),
            ComputeUnit.NPU: queue.PriorityQueue()
        }
        self.active_workers = {
            ComputeUnit.CPU: 0,
            ComputeUnit.GPU: 0,
            ComputeUnit.NPU: 0
        }
        self.scheduling_lock = threading.Lock()
        
        # Scheduling parameters
        self.cpu_threshold = 80  # Don't add CPU work if usage > 80%
        self.gpu_threshold = 85  # Don't add GPU work if usage > 85%
        self.memory_reserve_mb = 1024  # Reserve 1GB memory
        
        # Performance history for adaptive scheduling
        self.performance_history = {
            ComputeUnit.CPU: [],
            ComputeUnit.GPU: [],
            ComputeUnit.NPU: []
        }
        
    def start(self):
        """Start the scheduler"""
        self.resource_monitor.start()
        print("Intelligent scheduler started")
        
    def stop(self):
        """Stop the scheduler"""
        self.resource_monitor.stop()
        print("Intelligent scheduler stopped")
        
    def submit_work(self, batch: WorkBatch) -> bool:
        """Submit work batch to appropriate queue"""
        with self.scheduling_lock:
            # Check if compute unit is available
            if self._can_schedule(batch):
                # Adjust priority based on current load
                adjusted_priority = self._calculate_dynamic_priority(batch)
                queue_item = (adjusted_priority, time.time(), batch)
                self.work_queues[batch.compute_unit].put(queue_item)
                return True
            else:
                # Try to reschedule to different compute unit
                alternative_unit = self._find_alternative_compute_unit(batch)
                if alternative_unit:
                    batch.compute_unit = alternative_unit
                    adjusted_priority = self._calculate_dynamic_priority(batch)
                    queue_item = (adjusted_priority, time.time(), batch)
                    self.work_queues[alternative_unit].put(queue_item)
                    return True
                return False
                
    def get_next_work(self, compute_unit: ComputeUnit) -> Optional[WorkBatch]:
        """Get next work item for specified compute unit"""
        try:
            _, _, batch = self.work_queues[compute_unit].get_nowait()
            return batch
        except queue.Empty:
            return None
            
    def _can_schedule(self, batch: WorkBatch) -> bool:
        """Check if work can be scheduled on requested compute unit"""
        state = self.resource_monitor.get_current_state()
        
        if batch.compute_unit == ComputeUnit.CPU:
            return (state.cpu_usage < self.cpu_threshold and 
                    state.cpu_available_cores > 0 and
                    state.system_memory_free > batch.memory_requirement + self.memory_reserve_mb * 1024 * 1024)
                    
        elif batch.compute_unit == ComputeUnit.GPU:
            return (state.gpu_usage < self.gpu_threshold and
                    state.gpu_memory_free > batch.memory_requirement and
                    self.active_workers[ComputeUnit.GPU] < 2)  # Limit concurrent GPU work
                    
        elif batch.compute_unit == ComputeUnit.NPU:
            return (state.npu_usage < 70 and  # Conservative NPU threshold
                    self.active_workers[ComputeUnit.NPU] < 1)  # Only one NPU task at a time
                    
        return False
        
    def _find_alternative_compute_unit(self, batch: WorkBatch) -> Optional[ComputeUnit]:
        """Find alternative compute unit if primary is busy"""
        state = self.resource_monitor.get_current_state()
        
        # Priority order for alternatives based on current load
        alternatives = []
        
        if batch.compute_unit != ComputeUnit.CPU and state.cpu_usage < self.cpu_threshold:
            alternatives.append((ComputeUnit.CPU, state.cpu_usage))
            
        if batch.compute_unit != ComputeUnit.GPU and state.gpu_usage < self.gpu_threshold:
            alternatives.append((ComputeUnit.GPU, state.gpu_usage))
            
        if batch.compute_unit != ComputeUnit.NPU and state.npu_usage < 70:
            alternatives.append((ComputeUnit.NPU, state.npu_usage))
        
        # Return least loaded alternative
        if alternatives:
            alternatives.sort(key=lambda x: x[1])
            return alternatives[0][0]
            
        return None
        
    def _calculate_dynamic_priority(self, batch: WorkBatch) -> int:
        """Calculate dynamic priority based on system state and history"""
        base_priority = batch.priority
        state = self.resource_monitor.get_current_state()
        
        # Adjust priority based on resource availability
        if batch.compute_unit == ComputeUnit.CPU:
            if state.cpu_usage > 60:
                base_priority += 10  # Lower priority when CPU is busy
                
        elif batch.compute_unit == ComputeUnit.GPU:
            if state.gpu_usage > 50:
                base_priority += 5
                
        # Consider recent performance history
        recent_performance = self._get_recent_performance(batch.compute_unit)
        if recent_performance < 0.5:  # Poor recent performance
            base_priority += 15
            
        return base_priority
        
    def _get_recent_performance(self, compute_unit: ComputeUnit) -> float:
        """Get recent performance metric for compute unit"""
        history = self.performance_history[compute_unit]
        if not history:
            return 1.0
            
        # Return average of last 5 measurements
        recent = history[-5:]
        return sum(recent) / len(recent)
        
    def record_performance(self, compute_unit: ComputeUnit, 
                          processing_time: float, batch_size: int):
        """Record performance for adaptive scheduling"""
        performance = batch_size / processing_time if processing_time > 0 else 0
        self.performance_history[compute_unit].append(performance)
        
        # Keep only recent history
        if len(self.performance_history[compute_unit]) > 20:
            self.performance_history[compute_unit] = self.performance_history[compute_unit][-20:]
            
    def register_worker_start(self, compute_unit: ComputeUnit):
        """Register that a worker started on compute unit"""
        with self.scheduling_lock:
            self.active_workers[compute_unit] += 1
            
    def register_worker_end(self, compute_unit: ComputeUnit):
        """Register that a worker finished on compute unit"""
        with self.scheduling_lock:
            self.active_workers[compute_unit] = max(0, self.active_workers[compute_unit] - 1)
            
    def get_scheduling_stats(self) -> Dict:
        """Get current scheduling statistics"""
        state = self.resource_monitor.get_current_state()
        
        return {
            'resource_state': {
                'cpu_usage': state.cpu_usage,
                'cpu_available_cores': state.cpu_available_cores,
                'gpu_usage': state.gpu_usage,
                'gpu_memory_free_mb': state.gpu_memory_free / (1024 * 1024),
                'system_memory_free_gb': state.system_memory_free / (1024**3)
            },
            'active_workers': dict(self.active_workers),
            'queue_sizes': {
                unit.value: self.work_queues[unit].qsize() 
                for unit in ComputeUnit
            },
            'performance_averages': {
                unit.value: (sum(self.performance_history[unit]) / len(self.performance_history[unit]) 
                           if self.performance_history[unit] else 0)
                for unit in ComputeUnit
            }
        }


class AdaptiveLoadBalancer:
    """
    Adaptive load balancer that learns from performance and adjusts distribution
    """
    
    def __init__(self, scheduler: IntelligentScheduler):
        self.scheduler = scheduler
        self.distribution_weights = {
            ComputeUnit.CPU: 0.4,
            ComputeUnit.GPU: 0.4,
            ComputeUnit.NPU: 0.2
        }
        self.learning_rate = 0.1
        
    def update_distribution(self, performance_results: Dict[ComputeUnit, float]):
        """Update distribution weights based on performance results"""
        total_performance = sum(performance_results.values())
        
        if total_performance > 0:
            # Calculate ideal distribution based on performance
            for unit in ComputeUnit:
                performance = performance_results.get(unit, 0)
                ideal_weight = performance / total_performance
                current_weight = self.distribution_weights[unit]
                
                # Adaptive update with learning rate
                new_weight = current_weight + self.learning_rate * (ideal_weight - current_weight)
                self.distribution_weights[unit] = max(0.1, min(0.8, new_weight))
            
            # Normalize weights
            total_weight = sum(self.distribution_weights.values())
            for unit in ComputeUnit:
                self.distribution_weights[unit] /= total_weight
                
    def get_recommended_distribution(self, total_batches: int) -> Dict[ComputeUnit, int]:
        """Get recommended batch distribution"""
        distribution = {}
        remaining_batches = total_batches
        
        for unit in ComputeUnit:
            if unit == ComputeUnit.NPU:  # NPU gets remaining batches
                distribution[unit] = remaining_batches
            else:
                batch_count = int(total_batches * self.distribution_weights[unit])
                distribution[unit] = batch_count
                remaining_batches -= batch_count
                
        return distribution


def create_optimized_scheduler() -> IntelligentScheduler:
    """Create and configure an optimized scheduler"""
    scheduler = IntelligentScheduler()
    
    # Tune for genome analysis workload
    scheduler.cpu_threshold = 85  # Allow higher CPU usage for compute-intensive work
    scheduler.gpu_threshold = 90  # GPU can handle high utilization
    scheduler.memory_reserve_mb = 2048  # Reserve more memory for large datasets
    
    return scheduler


def main():
    """Test the resource scheduler"""
    print("Testing Resource Scheduler")
    print("=" * 40)
    
    scheduler = create_optimized_scheduler()
    scheduler.start()
    
    try:
        # Create test work batches
        test_batches = [
            WorkBatch("cpu_1", {"data": "test"}, 1, ComputeUnit.CPU, 1.0, 100 * 1024 * 1024),
            WorkBatch("gpu_1", {"data": "test"}, 2, ComputeUnit.GPU, 0.5, 500 * 1024 * 1024),
            WorkBatch("npu_1", {"data": "test"}, 3, ComputeUnit.NPU, 0.8, 200 * 1024 * 1024),
        ]
        
        # Submit work
        for batch in test_batches:
            success = scheduler.submit_work(batch)
            print(f"Batch {batch.batch_id} scheduled: {success}")
        
        # Monitor for a few seconds
        time.sleep(3)
        
        # Print statistics
        stats = scheduler.get_scheduling_stats()
        print("\nScheduling Statistics:")
        print(f"CPU Usage: {stats['resource_state']['cpu_usage']:.1f}%")
        print(f"GPU Usage: {stats['resource_state']['gpu_usage']:.1f}%")
        print(f"Active Workers: {stats['active_workers']}")
        print(f"Queue Sizes: {stats['queue_sizes']}")
        
    finally:
        scheduler.stop()


if __name__ == "__main__":
    main()