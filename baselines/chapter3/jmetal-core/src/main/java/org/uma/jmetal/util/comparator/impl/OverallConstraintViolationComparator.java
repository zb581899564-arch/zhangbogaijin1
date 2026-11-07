package org.uma.jmetal.util.comparator.impl;

import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.comparator.ConstraintViolationComparator;
import org.uma.jmetal.util.solutionattribute.impl.OverallConstraintViolation;

/**
 * This class implements a <code>Comparator</code> (a method for comparing <code>Solution</code> objects)
 * based on the overall constraint violation of the solutions, as done in NSGA-II.
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */
@SuppressWarnings("serial")
public class OverallConstraintViolationComparator<S extends Solution<?>>
    implements ConstraintViolationComparator<S> {
  private OverallConstraintViolation<S> overallConstraintViolation ;

  /**
   * Constructor
   */
  public OverallConstraintViolationComparator() {
    overallConstraintViolation = new OverallConstraintViolation<S>() ;
  }

  /**
   * Compares two solutions. If the solutions has no constraints the method return 0
   *
   * @param solution1 Object representing the first <code>Solution</code>.
   * @param solution2 Object representing the second <code>Solution</code>.
   * @return -1, or 0, or 1 if o1 is less than, equal, or greater than o2,
   * respectively.
   */
  public int compare(S solution1, S solution2) {
//    System.out.println(solution1);
//    System.out.println(solution2);
//    System.out.println(overallConstraintViolation);

    double violationDegreeSolution1 ;
    double violationDegreeSolution2;
    if (overallConstraintViolation.getAttribute(solution1) == null) {
      return 0 ;
    }
    violationDegreeSolution1 =  overallConstraintViolation.getAttribute(solution1);
    violationDegreeSolution2 = overallConstraintViolation.getAttribute(solution2);
//    System.out.println(overallConstraintViolation);
//    System.out.println(violationDegreeSolution2);


//    try {
//      Thread.sleep(999999);
//    } catch (InterruptedException e) {
//      throw new RuntimeException(e);
//    }


    if ((violationDegreeSolution1 < 0) && (violationDegreeSolution2 < 0)) {
      if (violationDegreeSolution1 > violationDegreeSolution2) {
        return -1;
      } else if (violationDegreeSolution2 > violationDegreeSolution1) {
        return 1;
      } else {
        return 0;
      }
    } else if ((violationDegreeSolution1 == 0) && (violationDegreeSolution2 < 0)) {
      return -1;
    } else if ((violationDegreeSolution1 < 0) && (violationDegreeSolution2 == 0)) {
      return 1;
    } else {
      return 0;
    }
  }

  /*public int compare(Solution solution1, Solution solution2) {
    int betterInFirst = 0;
    int betterInSecond = 0;

    // Extract the objective values for the three objectives
    double obj1_1 = solution1.getObjective(0);
    double obj1_2 = solution1.getObjective(1);
    double obj1_6 = solution1.getObjective(6);

    double obj2_1 = solution2.getObjective(0);
    double obj2_2 = solution2.getObjective(1);
    double obj2_6 = solution2.getObjective(6);

    // Compare the objective values
    if (obj1_1 < obj2_1) {
      betterInFirst++;
    } else if (obj1_1 > obj2_1) {
      betterInSecond++;
    }

    if (obj1_2 < obj2_2) {
      betterInFirst++;
    } else if (obj1_2 > obj2_2) {
      betterInSecond++;
    }

    if (obj1_6 < obj2_6) {
      betterInFirst++;
    } else if (obj1_6 > obj2_6) {
      betterInSecond++;
    }

    // Determine the dominance relationship
    if (betterInFirst > 0 && betterInSecond == 0) {
      return -1; // solution1 dominates solution2
    } else if (betterInSecond > 0 && betterInFirst == 0) {
      return 1;  // solution2 dominates solution1
    } else {
      return 0;  // neither solution dominates the other
    }
  }*/



}
