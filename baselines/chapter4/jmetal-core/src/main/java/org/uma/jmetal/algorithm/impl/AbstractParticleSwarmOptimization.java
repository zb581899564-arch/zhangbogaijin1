package org.uma.jmetal.algorithm.impl;

import org.uma.jmetal.algorithm.Algorithm;

import java.util.List;

/**
 * Abstract class representing a PSO algorithm
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */
@SuppressWarnings("serial")
public abstract class AbstractParticleSwarmOptimization<S, Result> implements Algorithm <Result> {
  private List<S> swarm;
  public List<S> getSwarm() {
    return swarm;
  }
  public void setSwarm(List<S> swarm) {
    this.swarm = swarm;
  }

  protected abstract void initProgress() ;
  protected abstract void updateProgress() ;

  protected abstract boolean isStoppingConditionReached() ;
  protected abstract List<S> createInitialSwarm() ;
  protected abstract List<S> evaluateSwarm(List<S> swarm) ;
  protected abstract void initializeLeader(List<S> swarm);
  protected abstract void initializeParticlesMemory(List<S> swarm) ;
  protected abstract void initializeVelocity(List<S> swarm) ;
  protected abstract void updateVelocity(List<S> swarm) ;
  protected abstract void updatePosition(List<S> swarm) ;
  protected abstract void perturbation(List<S> swarm) ;
  protected abstract void updateLeaders(List<S> swarm);
  protected abstract void updateParticlesMemory(List<S> swarm) ;


  @Override
  public abstract Result getResult() ;

  @Override
  public void run() {
    swarm = createInitialSwarm() ;    //创建初始种群
    swarm = evaluateSwarm(swarm);    //相当于计算两个目标值
    initializeVelocity(swarm);
    initializeParticlesMemory(swarm) ;    //初始化历史最优解
    initializeLeader(swarm) ;   //初始化全局最优解，可以在这里调用初始化Q表的方法

    initProgress();         //第一次进化次数就是种群大小




    while (!isStoppingConditionReached()) {
      long startTime = System.currentTimeMillis();//新加的计时用的


      updateVelocity(swarm) ;     //分群更新速度    更新pbest gbest
      updatePosition(swarm) ;     //全局搜索
      perturbation(swarm) ;    // 加DE操作  就是局部搜索
      swarm = evaluateSwarm(swarm) ;
      updateLeaders(swarm) ;      //历史最优解
      updateParticlesMemory(swarm) ;    //全局最优解
      updateProgress();


      long endTime = System.currentTimeMillis();
      long executionTimeMs = endTime - startTime;
      // 将毫秒转换为分钟和秒
      int minutes = (int) (executionTimeMs / 60000); // 1 分钟 = 60000 毫秒
      int seconds = (int) ((executionTimeMs % 60000) / 1000); // 剩余的毫秒转换为秒
      int remainingMilliseconds = (int) (executionTimeMs % 1000); // 剩余的毫秒
      // 输出结果
      System.out.printf("方法执行时间: %d 分钟 %d 秒 %d 毫秒%n", minutes, seconds, remainingMilliseconds);
    }
  }
}
