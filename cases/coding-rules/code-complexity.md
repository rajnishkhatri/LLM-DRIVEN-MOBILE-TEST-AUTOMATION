---
type: analysis
title: 'Architecture and Code-Level Metrics'
description: 'Code-level metrics (cyclomatic complexity, coupling, abstractness, instability, distance from the main sequence) architects use to evaluate code-base structure and fitness functions.'
tags: [coding-rules, architecture]
---

5. Architecture And Code-Level Metrics
Software architecture, when implemented, consists at least partially of source code, so it seems natural that architects should utilize some code-level metrics to learn about the macro- and micro-level structure of their code bases. Many teams wire metrics tools into their continuous integration pipelines to gather code-level metrics. However, merely gathering metrics does not create a fitness function—​remember, a fitness function must have an objective measure. Thus, while measuring key metrics is good, setting alarms for concerning ranges converts them into fitness functions (and therefore a feedback loop).

Software architects are often envious of other engineering disciplines that have entire branches of mathematics devoted to them. We don’t have anything nearly so powerful (yet–give us a few centuries and we’re sure to come up with some better measurements). However, we can leverage a few source-code-derived metrics to look at important aspects of our code bases.

While safeguarding code quality has always been a concern and responsibility of software architects, it’s more important than ever now that artificial intelligence writes more and more actual implementation code. Architects need metrics to look for the negative aspects of generated code (like brute force, lack of abstraction, and other problems). This chapter thus provides a few metrics that can expose “AI slop” code in your ecosystem.

Cyclomatic Complexity

is a code-level metric designed by Thomas McCabe in 1976 to provide an objective measure for the complexity of code at the function/method, class, or application level. It is computed by applying graph theory to code—specifically, to decision points, which cause different execution paths. For example, if a function has no decision statements (such as if statements), then CC = 1. If the function has a single conditional, then CC = 2 because there are two possible execution paths.

The formula for calculating the CC for a single function or method is , where N represents nodes (lines of code), and E represents edges (possible decisions). Consider the C-like code shown in Example 5-1:

Example 5-1. Sample code for evaluating cyclomatic complexity

public void decision(int c1, int c2) {
    if (c1 < 100)
        return 0;
    else if (c1 + C2 > 500)
       return 1;
    else
      return -1;
}
The CC for Example 5-1 is 3 (3 – 2 + 2), shown in Figure 5-1.

eng cc
Figure 5-1. Cyclomatic complexity graph for the decision function

The number 2 in the CC formula represents a simplification of a single function/method. For fan-out calls to other methods (known as connected components in graph theory), the more general formula is , where P represents the number of connected components.

CC is a great example of the bluntness of the metrics available to architects, as we alluded to above. While it measures the complexity of code, CC cannot determine whether that complexity is essential (because we’re solving a complicated problem) or accidental (because we’ve implemented a poor design). Metrics like CC are extremely useful for assessing code, however, whether it’s written by developers or generative AI. Generative AI tends to solve problems by brute force, which often leads to accidental complexity. For example, if a developer asks a coding assistant to generate a unique case for a rule for each of the 50 US states, it will gleefully provide a 50-state switch statement rather than using something like the .

Architects and developers universally agree that overly complex code is undesirable. It harms modularity, testability, deployability–in fact, virtually every one of the desirable characteristics of code bases. If teams don’t keep an eye on gradually growing complexity, it will dominate the code base. But that begs the question: How bad is too bad?

Of course, like all questions in software architecture, the answer is: it depends! Specifically, it depends on the complexity of the problem domain. For example, if you have an algorithmically complex problem, the solution will yield complex functions. Are those functions complex because of the problem domain or because of poor coding? Alternatively, is the code partitioned poorly? Could a large method be broken down into smaller logical chunks, distributing the work (and complexity) into more well-factored methods?

In general, the industry thresholds for CC suggest that a value under 10 is acceptable (barring other considerations, such as complex domains). We consider that threshold very high and would prefer code to fall under five, indicating cohesive, well-factored code. A metrics tool in the Java world, , attempts to determine how poor (crappy) your code is by evaluating a combination of CC and code coverage; if the CC grows to over 50, no amount of code coverage rescues that code from crappiness. The most terrifying professional artifact Neal has ever encountered was a single C function with over 4,000 lines of code, including liberal use of GOTO statements (to escape impossibly deeply nested loops). It served as the heart of a commercial software package whose CC was over 800! .

Engineering practices like test-driven development (TDD) have the beneficial side effect of generating smaller, less complex methods on average for a given problem domain. Developers practicing TDD try to write a simple test, then write the smallest amount of code that will pass the test. This focus on discrete behavior and good test boundaries encourages well-factored, highly cohesive methods that exhibit low CC.

A wide variety of metrics tools geared toward specific platforms and technology stacks can help defend against overly high CC. In ADL, an architect could express CC intent:

Example 5-2. Restricting cyclomatic complexity to under a threshold value

define MAX_CYCLOMATIC_COMPLEXITY = 10

foreach component : comp in system
    foreach class : cls in comp
        foreach method : m in class
            (assert cyclomatic complexity of m < MAX_CYCLOMATIC_COMPLEXITY)
	endfor
    endfor
endfor
In Example 5-2, because CC is a method-level metric, we dig into each component and each class to determine the CC of each method. This check does not distinguish between essential and accidental complexity and may generate too many false failures. Architects could adopt a more holistic approach and look for the average CC in some project-specific aggregated view, as expressed in Example 5-3:

Example 5-3. Using the average C` instead of measuring each method.

define MAX_CYCLOMATIC_COMPLEXITY = 10

foreach component : comp in system
    foreach class : cls in comp
        (assert average cyclomatic complexity for cls < MAX_CYCLOMATIC_COMPLEXITY)
    endfor
endfor
Cyclomatic complexity is one of the best indicators that a code base is overusing AI-generated code. Architects should consider segregating code written by coding assistants and apply more rigorous code-quality metrics to it.

Coupling

Edward Yourdon and Larry Constantine’s book Structured Design: Fundamentals of a Discipline of Computer Program and Systems Design (Prentice-Hall, 1979) defined many core concepts, including the metrics afferent coupling and efferent coupling. Afferent coupling measures the number of incoming connections to a code artifact (component, class, function, and so on). Efferent coupling measures outgoing connections to other code artifacts. There are tools for virtually every platform that allow architects to analyze and build fitness functions around the coupling characteristics of code. However, except in degenerate cases, these metrics don’t provide much holistic insight. For example, an architect restructuring an architecture from one style to another will greatly benefit from tools that show afferent and efferent coupling. However, it is difficult to derive a general value divorced from a problem domain.

The complementary concept to coupling is cohesion, which measures whether code artifacts should be co-located. Developers often make judgment calls about cohesion, except in obvious cases of accidental cohesion—​for example, when several classes appear randomly within a component and share nothing, like the various classes that end with Utils in many projects.

While these two coupling metrics are useful for analyzing existing code bases, several derived metrics provide more valuable holistic insight. The metrics discussed in the next few sections were created by software engineer and apply widely to most object-oriented languages.

Abstractness

Abstractness is the ratio of abstract artifacts (abstract classes, interfaces, and so on) to concrete artifacts (implementation or actual executable lines of code). Class definitions, interfaces, even method names aren’t concrete code but abstractions. For example, we could refactor a ten-line method into five two-line methods and never add any actual behavior to the system–merely abstractions. The Abstractness metric measures a code base’s degree of abstractness versus implementation. On one end of the scale would be a code base with no abstractions, just a huge, single function (as in a single main() method). The other end of the scale would be a code base with too many abstractions, making it difficult for developers to understand how things are wired together, as in a case where every method has only one or two lines of code.

The formula for Abstractness is a ratio of the sum of abstract artifacts to the sum of concrete and abstract ones:

Equation 5-1. Abstractness


In the equation above, represents abstract elements (interfaces or abstract classes) within the module, and represents concrete elements (nonabstract classes). This indicates how much of the code base is present to help readers understand the rest of the code base.

Abstractness is a particular weakness of generative AI code, which tends to default to solving problems by brute force. For example, a 200-line method consisting of a huge 50-stage switch statement would score poorly on the Abstractness metric; a code base utilizing the Strategy design pattern would score much better.

Instability

Another derived metric, Instability, is defined as the ratio of efferent coupling to the sum of both efferent and afferent coupling, as shown in Equation 5-2.

Equation 5-2. Instability


In this equation, represents efferent (or outgoing) coupling, and represents afferent (or incoming) coupling.

The Instability metric determines the volatility of a code base. A code base that exhibits high degrees of instability breaks more easily when changed because it is highly coupled. For example, if a class calls too many other classes to delegate work, the calling class will be highly susceptible to breakage if one or more of the called methods changes.

Instability is an indicator of how much reuse is present within a code base. For example, a component with an instability of zero is completely stable, which sounds nice…​ but it also means zero code is being reused, suggesting that its developers have gone back to using a single massive main() method. However, too much reuse is also bad. What architects need is a way to assess the balance between abstractness and instability.

Normalized Distance from the Main Sequence

One of the few holistic metrics architects have for architectural structure is Normalized Distance from the Main Sequence, a derived metric based on instability and abstractness, shown in Equation 5-3. We’ll call it the Distance metric for brevity.

Equation 5-3. Normalized Distance from the Main Sequence


In the equation, = Abstractness and = Instability.

When an architect evaluates a component, they derive values for both abstractness and instability, placing a point in the two-dimensional space, as shown in Figure 5-2.


Figure 5-2. The main sequence defines the ideal relationship between Abstractness and Instability

The Distance metric imagines an ideal relationship between Abstractness and Instability; classes that fall near this ideal line exhibit a healthy mixture of these two competing concerns. For example, graphing a particular class allows developers to calculate its Distance metric, illustrated in Figure 5-3.


Figure 5-3. Normalized Distance from the Main Sequence for a particular class

The Distance metric graphs the candidate class, then measures its distance from the idealized line. The closer to the line, the better balanced the class. Classes that fall too far into the upper right-hand corner enter what architects call the Zone of Uselessness, where code that is too abstract becomes difficult to use. Conversely, code that falls into the lower left-hand corner enters the Zone of Pain: with too much implementation and not enough abstraction, it becomes brittle and hard to maintain.


Figure 5-4. The Zones of Uselessness and Pain

What does code in the Zone of Uselessness quadrant look like? It has too many abstractions and too much instability, leading to either the kind of code base where each method is quite small or a code case that utilizes a lot of indirection, such as testing libraries. It’s rare for code to fall into this quadrant.

However, the other boundary case, the Zone of Pain, is all too common. What does that code look like? Too little abstraction (in other words, large methods) and too little instability (not enough reuse). The Zone of Pain is a clear indicator of too much AI-generated code.

Many platforms provide tools to calculate these measures. Architects use them when analyzing code bases to get familiar with them, prepare them for a migration, or assess their technical debt.

Our practice is to state our intent first in ADL, as shown in Example 5-4:

Example 5-4. Defining a threshold for normalized distance from the main sequence

define MAX_DISTANCE = .3

system Order_Placement

foreach Compoent : C in Order_Placement
    (assert that normalized distance from the main sequeence for c < MAX_DISTANCE)
endfor
In Example 5-4, we define the system and then apply the metric to each component, checking it against our defined threshold. We can then generate a concrete fitness function for this structural feedback that calculates intermediate values of abstractness and instability, which it will ultimately use to calculate normalized distance. An example of a concrete fitness function for Java appears in Example 5-5:

Example 5-5. A concrete Java implementation of the main sequence metric

  private static final double MAX_DISTANCE = 0.3;

  @ArchTest
  public void components_must_have_normalized_distance_less_than_max() {
      allClasses()
          .should(haveNormalizedDistanceLessThan(MAX_DISTANCE))
          .check(ArchUnit.getClasses()));
  }
  
private static ArchCondition<JavaClass> haveNormalizedDistanceLessThan(double maxDistance) {
      return new ArchCondition<JavaClass>("have normalized distance D < " + maxDistance) {
          @Override
          public void check(JavaClass javaClass, ConditionEvents events) {
              String packageName = javaClass.getPackage().getName();
              
              double abstractnessA = calculateAbstractness(javaClass, javaClass.getClasses()); 1
              double instabilityI = calculateInstability(javaClass, javaClass.getClasses());   2
              
              double normalizedDistance = Math.abs(abstractnessA + instabilityI - 1.0);
              
              if (normalizedDistance > maxDistance) {
                  String message = String.format(
                      "Package exceeds the max distance of %.3f",
                      packageName, normalizedDistance, abstractnessA, instabilityI, maxDistance
                  );
                  events.add(SimpleConditionEvent.violated(javaClass, message));
              } else {
                  events.add(SimpleConditionEvent.satisfied(javaClass, ""));
              }
          }
      };
}
1
Placeholder for the Abstractness metric

2
Placeholder for the Instability metric

This code builds the test condition using the ArchUnit API. However, rather than implement our own Abstractness and Instability metrics, we have instead created abstract method placeholders for those values, passing all the relevant classes as parameters. We do this for a couple of reasons. First, architects should not use generative AI to generate deterministic things. Both metrics are well established and have plentiful tools (including open-source ones for most platforms), making it a waste to have AI generate a bespoke implementation. Second, the main point of this check is the overall metric of the main sequence, so it is wise not to take on more details than necessary.

Normalized Distance from the Main Sequence is one of the few concrete, code-derived metrics architects have to find poorly structured code, whether created by human or machine. It is an excellent overall structural-quality metric for architects to wire into their continuous builds.