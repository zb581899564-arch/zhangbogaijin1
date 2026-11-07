"""Local state/storage harness only; original archive and comparison bodies are extracted separately."""
PREFIX = r'''
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#define FALSE 0
#define TRUE 1
#define MINIMIZATION 1
#define MAXIMIZATION 2
int number_of_objectives=3, number_of_parameters=2, elitist_archive_size;
int directions[3]={1,1,1}, *optimization=directions;
int objective_discretization_in_effect;
char elitist_archive_front_changed;
double widths[3]={1,1,1}, *objective_discretization=widths;
double objectives[32][3], *objective_pointers[32], constraints[32];
double **elitist_archive_objective_values=objective_pointers;
double *elitist_archive_constraint_values=constraints;
char genes[32][2], *gene_pointers[32], **elitist_archive=gene_pointers;
void *Malloc(size_t size){return malloc(size);}
void addToElitistArchive(char *solution,double *obj,double con){
    int j,n=elitist_archive_size++;for(j=0;j<3;j++)objectives[n][j]=obj[j];
    for(j=0;j<2;j++)genes[n][j]=solution[j];constraints[n]=con;
}
void removeFromElitistArchive(int *indices,int count){
    int old,new_size=0,j,k,remove;
    for(old=0;old<elitist_archive_size;old++){
        remove=0;for(k=0;k<count;k++)if(indices[k]==old)remove=1;
        if(!remove){for(j=0;j<3;j++)objectives[new_size][j]=objectives[old][j];
            for(j=0;j<2;j++)genes[new_size][j]=genes[old][j];
            constraints[new_size++]=constraints[old];}
    }elitist_archive_size=new_size;
}
'''

MAIN = r'''
int main(int argc,char **argv){
    FILE *input=fopen(argv[1],"r");int id,grid,n,i,j;double parent[3],candidate[3],zero=0;
    char is_new,is_dominated,proposal[2]={0,1};if(!input)return 2;
    for(i=0;i<32;i++){objective_pointers[i]=objectives[i];gene_pointers[i]=genes[i];}
    while(fscanf(input,"%d%d%d",&id,&grid,&n)==3){
        elitist_archive_size=n;objective_discretization_in_effect=grid;elitist_archive_front_changed=FALSE;
        for(i=0;i<n;i++){for(j=0;j<3;j++)if(fscanf(input,"%lf",&objectives[i][j])!=1)return 3;
            constraints[i]=0;genes[i][0]=genes[i][1]=(char)i;}
        for(j=0;j<3;j++)if(fscanf(input,"%lf",&parent[j])!=1)return 4;
        for(j=0;j<3;j++)if(fscanf(input,"%lf",&candidate[j])!=1)return 5;
        updateElitistArchiveWithReplacementOfExistedMember(proposal,candidate,zero,&is_new,&is_dominated);
        printf("%d,%d,%d,%d,%d\n",id,is_new,is_dominated,elitist_archive_size,
            constraintWeaklyParetoDominates(candidate,zero,parent,zero)||!is_dominated);
    }fclose(input);return 0;
}
'''
