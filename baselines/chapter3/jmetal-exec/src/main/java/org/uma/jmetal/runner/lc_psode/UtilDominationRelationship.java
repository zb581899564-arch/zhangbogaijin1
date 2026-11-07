package org.uma.jmetal.runner.lc_psode;

import org.uma.jmetal.problem.multiobjective.dfsp.DHFSP;
import org.uma.jmetal.solution.PermutationSolution;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;


public class UtilDominationRelationship {

    private int problemflag=7;
    private int jobs=50;
    private int machines=10;
    private int snumber=1;

/*    public void shuchu(List<PermutationSolution<Integer>> population, String algorithmname) throws IOException {

        BufferedWriter bw = new BufferedWriter(new FileWriter("F:\\晨\\PSO算法研究\\PSO+DFSP\\"+problemflag+"_"+jobs+"_"+machines+"_"+snumber+"-"+algorithmname+".txt",true));
        for(int i=0;i<population.size();i++){
            bw.write(population.get(i).getObjective(0)+" "+population.get(i).getObjective(1)+"      ");
            for(int j=0;j<population.get(i).getNumberOfVariablesid();j++){
                bw.write(population.get(i).getVariableValue(j)+" ");
            }
            bw.newLine();
        }
        bw.newLine();

        bw.flush();
        bw.close();
    }*/

    public void shuchu(List<PermutationSolution<Integer>> population, String algorithmname,int jobs,int machines,int snumber,String datafile) throws IOException {
        BufferedWriter bw = new BufferedWriter(new FileWriter(datafile+jobs+"_"+machines+"_"+snumber+"-"+algorithmname+".txt",true));
        for(int i=0;i<population.size();i++){
            bw.write(population.get(i).getObjective(0)+" "+population.get(i).getObjective(1)+"      ");
            for(int j=0;j<population.get(i).getNumberOfVariablesid();j++){    //以粒子的工件or工厂向量的大小来做循环  工件工厂向量一样大
                bw.write(population.get(i).getVariableValue(j)+" ");
            }

            bw.write("   ***");
            for(int j=0;j<population.get(i).getNumberOfVariablesid();j++){    //以粒子的工件or工厂向量的大小来做循环  工件工厂向量一样大
                bw.write(population.get(i).getVariableValueid(j)+" ");
            }  //自己屏蔽粒子

            bw.newLine();
        }
        bw.newLine();

        bw.flush();
        bw.close();
    }

    //带r1\r2参数
    public void outputSolution2File(double crossoverRate, double mutationRate, double rand_k,double pmxCrossover ,double V1mutationProbability, int swarmsize,
                                    double  DERate,double DEcrossoverRates,double DEmutationRate, List<PermutationSolution<Integer>> population, String algorithmname, int jobs, int numberOfStages, int numberOffactories, int snumber, String folderName) throws IOException {

        //BufferedWriter bw = new BufferedWriter(new FileWriter(datafile+jobs+"_"+machines+"_"+snumber+"-"+algorithmname+".txt",true));

        //带r1\r2参数
        StringBuilder sbFileName= new StringBuilder();
        sbFileName.append(folderName).append("solution-");
        sbFileName.append(jobs).append("_");
        sbFileName.append(numberOfStages).append("_");
        sbFileName.append(numberOffactories).append("_");
        sbFileName.append(snumber).append("_");
        sbFileName.append(algorithmname).append("_");
        sbFileName.append(rand_k).append("_");
        sbFileName.append(pmxCrossover).append("_");
        sbFileName.append(V1mutationProbability).append("_");
        sbFileName.append(swarmsize).append("_");
        sbFileName.append(crossoverRate).append("_");
        sbFileName.append(mutationRate).append("_");
        sbFileName.append(DERate).append("_");
        sbFileName.append(DEcrossoverRates).append("_");
        sbFileName.append(DEmutationRate);
        sbFileName.append(".txt");


        //BufferedWriter bw = new BufferedWriter(new FileWriter(folderName+jobs+"_"+machines+"_"+snumber+"-"+algorithmname+"_"+rand_k+"_"+swarmsize+"_"+Probability+"_"+crossoverRate+"_"+mutationRate+".txt",true));
        BufferedWriter bw = new BufferedWriter(new FileWriter(sbFileName.toString(),true));

        for(int i=0;i<population.size();i++){
            StringBuffer sb1 = new StringBuffer();
            sb1.append(population.get(i).getObjective(0)).append(" ").append(population.get(i).getObjective(1)).append("\t");
            //bw.write(population.get(i).getObjective(0)+" "+population.get(i).getObjective(1)+"      ");
            bw.write(sb1.toString());

            //job vector
            for(int j=0;j<population.get(i).getNumberOfVariables();j++){
                StringBuffer sb2= new StringBuffer();
                sb2.append(population.get(i).getVariableValue(j)).append(" ");
                //bw.write(population.get(i).getVariableValue(j)+" ");
                bw.write(sb2.toString());
            }
            bw.newLine();

            //factory vector
            bw.write("\t\t\t\t");
            for(int j=0;j<population.get(i).getNumberOfVariablesid();j++){
                StringBuffer sb3= new StringBuffer();
                sb3.append(population.get(i).getVariableValueid(j).toString()).append(" ");
                //bw.write(population.get(i).getVariableValue(j)+" ");
                bw.write(sb3.toString());
            }
            bw.newLine();
        }
        bw.newLine();

        bw.flush();
        bw.close();
    }

    public void outputSolution2FileNonparametric(double crossoverRate, double mutationRate, double rand_k,double pmxCrossover ,double V1mutationProbability, int swarmsize,
                                    double  DERate,double DEcrossoverRates,double DEmutationRate, List<PermutationSolution<Integer>> population, String algorithmname, int jobs, int stages, int factories, int snumber, String folderName) throws IOException {

        //BufferedWriter bw = new BufferedWriter(new FileWriter(datafile+jobs+"_"+machines+"_"+snumber+"-"+algorithmname+".txt",true));

        StringBuilder sbFileName= new StringBuilder();
        sbFileName.append(folderName).append("solution-");
        sbFileName.append(jobs).append("_");
        sbFileName.append(stages).append("_");
        sbFileName.append(factories).append("_");
        sbFileName.append(snumber).append("_");
        sbFileName.append(algorithmname).append("_");
        sbFileName.append(rand_k).append("_");
        sbFileName.append(pmxCrossover).append("_");
        sbFileName.append(V1mutationProbability).append("_");
        sbFileName.append(swarmsize).append("_");
        sbFileName.append(crossoverRate).append("_");
        sbFileName.append(mutationRate).append("_");
        sbFileName.append(DERate).append("_");
        sbFileName.append(DEcrossoverRates).append("_");
        sbFileName.append(DEmutationRate);
        sbFileName.append(".txt");


        //BufferedWriter bw = new BufferedWriter(new FileWriter(folderName+jobs+"_"+machines+"_"+snumber+"-"+algorithmname+"_"+rand_k+"_"+swarmsize+"_"+Probability+"_"+crossoverRate+"_"+mutationRate+".txt",true));
        BufferedWriter bw = new BufferedWriter(new FileWriter(sbFileName.toString(),true));

        System.out.println("搜索到了"+population.size()+"个解");
        for(int i=0;i<population.size();i++){

            StringBuffer sb1 = new StringBuffer();
//            sb1.append(population.get(i).getObjective(0)).append(" ").append(population.get(i).getObjective(1)).append(" ").append(population.get(i).getObjective1(0)).append("\n");
            sb1.append(population.get(i).getObjective(0)).append(" ").append(population.get(i).getObjective(1)).append(" ").append(population.get(i).getObjective(2)).append("\n");

            bw.write(sb1.toString());

            //job vector
            for(int j=0;j<population.get(i).getNumberOfVariables();j++){
                StringBuffer sb2= new StringBuffer();
                sb2.append(population.get(i).getVariableValue(j)).append(" ");
                bw.write(sb2.toString());
            }
            bw.newLine();

            //factory vector
            //bw.write("\t\t\t\t");
            for(int j=0;j<population.get(i).getNumberOfVariablesid();j++){
                StringBuffer sb3= new StringBuffer();
                sb3.append(population.get(i).getVariableValueid(j).toString()).append(" ");
                bw.write(sb3.toString());
            }
            bw.newLine();

            for(int j=0;j<population.get(i).getNumberOfVariablesworker();j++){
                StringBuffer sb3= new StringBuffer();
                sb3.append(population.get(i).getVariableValueworker(j).toString()).append(" ");
                bw.write(sb3.toString());
            }
//
//            //20241204
//            bw.newLine();
//            List<Integer> machine = (List<Integer>) population.get(i).getAttribute("machine");
//            for(int j=0;j<population.get(i).getNumberOfVariables();j++){
//                StringBuffer sb4= new StringBuffer();
//                sb4.append(machine.get(j).toString()).append(" ");
//                bw.write(sb4.toString());
//            }


            bw.newLine();
            bw.newLine();
        }
        bw.newLine();

        bw.flush();
        bw.close();

        /////////////////////////////////////////////////
        StringBuilder obFileName= new StringBuilder();
        obFileName.append(folderName).append("object-");
        obFileName.append(jobs).append("_");
        obFileName.append(stages).append("_");
        obFileName.append(factories).append("_");
        obFileName.append(snumber).append("-");
        obFileName.append(algorithmname).append("-");
        obFileName.append(rand_k).append("_");
        obFileName.append(pmxCrossover).append("_");
        obFileName.append(V1mutationProbability).append("_");
        obFileName.append(swarmsize).append("_");
        obFileName.append(crossoverRate).append("_");
        obFileName.append(mutationRate).append("_");
        obFileName.append(DERate).append("_");
        obFileName.append(DEcrossoverRates).append("_");
        obFileName.append(DEmutationRate);
        obFileName.append(".txt");

        BufferedWriter obw = new BufferedWriter(new FileWriter(obFileName.toString(),true));

        for(int i=0;i<population.size();i++){
            StringBuffer object = new StringBuffer();
            object.append(population.get(i).getObjective(0)).append(" ").append(population.get(i).getObjective(1)).append(" ").append(population.get(i).getObjective(2)).append("\t");
            obw.write(object.toString());
            obw.newLine();
        }

        obw.newLine();
        obw.flush();
        obw.close();
    }


    public void outputCPUTime(double computingTime, String algorithmname, int jobs, int numberOfStages, int numberOffactories,int snumber, String folderName) throws IOException {

        StringBuilder sbFileName= new StringBuilder();
        sbFileName.append(folderName).append("CPUTime.txt");

        //BufferedWriter bw = new BufferedWriter(new FileWriter(folderName+"time.txt",true));
        BufferedWriter bw = new BufferedWriter(new FileWriter(sbFileName.toString(),true));

        StringBuilder sb1= new StringBuilder();
        sb1.append(jobs).append("_").append(numberOfStages).append("_").append(numberOffactories).append("_").append(snumber).append(", ").append(algorithmname).append(", ");
        sb1.append(computingTime);

        //bw.write(jobs+"_"+machines+"_"+snumber+"-"+algorithmname+": "+computingTime);
        bw.write(sb1.toString());

        bw.newLine();
        bw.flush();
        bw.close();
    }

/*    public void addtoparetofile( List<PermutationSolution<Integer>> population, int problemflag, int jobs,
                                 int machines, int snumber, PermutationProblem<PermutationSolution<Integer>> problem,String paretofile) throws IOException {

        List<PermutationSolution<Integer>> pareto = readparetofile(population, problemflag, jobs, machines, snumber, problem, paretofile);//读paretofile中的数据
        pareto = nondominatecaozuo(pareto);

        //BufferedWriter bw = new BufferedWriter(new FileWriter("F:\\桌面杂项包\\0-PSO算法研究\\0-PSO-DFSP\\"+problemflag+"\\"+problemflag+"_"+jobs+"_"+machines+"_"+snumber+"-"+algorithmname+".txt",true));
        BufferedWriter bw = new BufferedWriter(new FileWriter(paretofile));

        for(int i=0;i<pareto.size();i++){
            bw.write(pareto.get(i).getObjective(0)+" "+pareto.get(i).getObjective(1));

            bw.newLine();
        }

        bw.flush();
        bw.close();

    }*/


    public List<PermutationSolution<Integer>> nondominatecaozuo (List<PermutationSolution<Integer>> population) {
        ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(population.size());

        for(int i=0;i<population.size();i++){
            A.add((PermutationSolution<Integer>) population.get(i).copy());
        }

        for(int i=0;i<A.size();i++){
            for(int j=i+1;j<A.size();j++){
                if(A.get(i).getObjective(0)<=A.get(j).getObjective(0)&&A.get(i).getObjective(1)<=A.get(j).getObjective(1)&&A.get(i).getObjective(2)<=A.get(j).getObjective(2)){
                    A.remove(j);
                    j--;
                }
            }
            for(int j=i+1;j<A.size();j++){
                if(A.get(i).getObjective(0)>=A.get(j).getObjective(0) && A.get(i).getObjective(1)>=A.get(j).getObjective(1)&& A.get(i).getObjective(2)>=A.get(j).getObjective(2)){
                    A.remove(i);
                    i--;
                    break;
                }
            }
        }
        return A;
    }

    public void outputSolution2FileNonparametricnew(double crossoverRate, double mutationRate, double rand_k,double pmxCrossover ,double V1mutationProbability, int swarmsize,
                                                 double  DERate,double DEcrossoverRates,double DEmutationRate, List<PermutationSolution<Integer>> population, String algorithmname, int jobs, int stages, int factories, int snumber, String folderName,double crossoverRates4worker,double crossoverRates4machine,
    double mutationRate4worker,double mutationRate4machine,int localsearch) throws IOException {

        //BufferedWriter bw = new BufferedWriter(new FileWriter(datafile+jobs+"_"+machines+"_"+snumber+"-"+algorithmname+".txt",true));

        StringBuilder sbFileName= new StringBuilder();
        sbFileName.append(folderName).append("solution-");
        sbFileName.append(jobs).append("_");
        sbFileName.append(stages).append("_");
        sbFileName.append(factories).append("_");
        sbFileName.append(snumber).append("_");
        sbFileName.append(algorithmname).append("_");
        sbFileName.append(rand_k).append("_");
        sbFileName.append(pmxCrossover).append("_");
        sbFileName.append(V1mutationProbability).append("_");
        sbFileName.append(swarmsize).append("_");
        sbFileName.append(crossoverRate).append("_");
        sbFileName.append(mutationRate).append("_");
        sbFileName.append(DERate).append("_");
        sbFileName.append(DEcrossoverRates).append("_");
        sbFileName.append(DEmutationRate).append("_");
        sbFileName.append(crossoverRates4worker).append("_");
        sbFileName.append(crossoverRates4machine).append("_");
        sbFileName.append(mutationRate4worker).append("_");
        sbFileName.append(mutationRate4machine).append("_");
        sbFileName.append(localsearch);
        sbFileName.append(".txt");


        //BufferedWriter bw = new BufferedWriter(new FileWriter(folderName+jobs+"_"+machines+"_"+snumber+"-"+algorithmname+"_"+rand_k+"_"+swarmsize+"_"+Probability+"_"+crossoverRate+"_"+mutationRate+".txt",true));
        BufferedWriter bw = new BufferedWriter(new FileWriter(sbFileName.toString(),true));

        System.out.println("搜索到了"+population.size()+"个解");
        for(int i=0;i<population.size();i++){

            StringBuffer sb1 = new StringBuffer();
//            sb1.append(population.get(i).getObjective(0)).append(" ").append(population.get(i).getObjective(1)).append(" ").append(population.get(i).getObjective1(0)).append("\n");
            sb1.append(population.get(i).getObjective(0)).append(" ").append(population.get(i).getObjective(1)).append(" ").append(population.get(i).getObjective(2)).append("\n");

            bw.write(sb1.toString());

            //job vector
            for(int j=0;j<population.get(i).getNumberOfVariables();j++){
                StringBuffer sb2= new StringBuffer();
                sb2.append(population.get(i).getVariableValue(j)).append(" ");
                bw.write(sb2.toString());
            }
            bw.newLine();

            //factory vector
            //bw.write("\t\t\t\t");
            for(int j=0;j<population.get(i).getNumberOfVariablesid();j++){
                StringBuffer sb3= new StringBuffer();
                sb3.append(population.get(i).getVariableValueid(j).toString()).append(" ");
                bw.write(sb3.toString());
            }
            bw.newLine();

            for(int j=0;j<population.get(i).getNumberOfVariablesworker();j++){
                StringBuffer sb3= new StringBuffer();
                sb3.append(population.get(i).getVariableValueworker(j).toString()).append(" ");
                bw.write(sb3.toString());
            }
//
//            //20241204
            bw.newLine();
            List<Integer> machine = (List<Integer>) population.get(i).getAttribute("machine");
            for(int j=0;j<population.get(i).getNumberOfVariables();j++){
                StringBuffer sb4= new StringBuffer();
                sb4.append(machine.get(j).toString()).append(" ");
                bw.write(sb4.toString());
            }


            bw.newLine();
            bw.newLine();
        }
        bw.newLine();

        bw.flush();
        bw.close();

        /////////////////////////////////////////////////
        StringBuilder obFileName= new StringBuilder();
        obFileName.append(folderName).append("object-");
        obFileName.append(jobs).append("_");
        obFileName.append(stages).append("_");
        obFileName.append(factories).append("_");
        obFileName.append(snumber).append("-");
        obFileName.append(algorithmname).append("-");
        obFileName.append(rand_k).append("_");
        obFileName.append(pmxCrossover).append("_");
        obFileName.append(V1mutationProbability).append("_");
        obFileName.append(swarmsize).append("_");
        obFileName.append(crossoverRate).append("_");
        obFileName.append(mutationRate).append("_");
        obFileName.append(DERate).append("_");
        obFileName.append(DEcrossoverRates).append("_");
        obFileName.append(DEmutationRate).append("_");
        obFileName.append(crossoverRates4worker).append("_");
        obFileName.append(crossoverRates4machine).append("_");
        obFileName.append(mutationRate4worker).append("_");
        obFileName.append(mutationRate4machine).append("_");
        obFileName.append(localsearch);
        obFileName.append(".txt");

        BufferedWriter obw = new BufferedWriter(new FileWriter(obFileName.toString(),true));

        for(int i=0;i<population.size();i++){
            StringBuffer object = new StringBuffer();
            object.append(population.get(i).getObjective(0)).append(" ").append(population.get(i).getObjective(1)).append(" ").append(population.get(i).getObjective(2)).append("\t");
            obw.write(object.toString());
            obw.newLine();
        }

        obw.newLine();
        obw.flush();
        obw.close();
    }




}
