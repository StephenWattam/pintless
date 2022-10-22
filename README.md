# Pintless
[![CodeFactor](https://www.codefactor.io/repository/github/stephenwattam/pintless/badge)](https://www.codefactor.io/repository/github/stephenwattam/pintless)
![Linting and building](https://github.com/StephenWattam/pintless/actions/workflows/python-package.yml/badge.svg)

The unit library [pint](https://github.com/hgrecco/pint) is fantastic.  It removes a whole class of bugs from common data science workloads, and provides good tools for humans to process numbers.  But it's very slow, and provides vast swaths of functionality that I don't need.

This library is like pint, but _less_ --- it lets you use units without pain, but aims to be performant and small-in-memory.  It's designed as a drop-in replacement to pint for those of us who don't use most of pint's features.

Choice of features is based on my personal experience in projects.  From this I've developed some principles that will be followed here to prevent creep/bloat:

Things this doesn't support:

 - unit groups: use a new definition file if you want this.
 - Units that don't scale from 0, e.g. degrees C and F.
 - LaTeX output
 - Translation to other languages --- want different units?  Use a different definition file
 - Simplification of units: algebraic simplifications are necessary, but choosing 'sensible' units for humans is beyond the scope of this lib
 - Scientific notation and other non-unit number representation problems.  This is a unit library and only deals with numbers because it has to to adjust the values therein.

Design Principles

 - Fast is more important than small or simple
 - Precompute where possible
 - Having principles usually leads you to design for them rather than reality
 - Don't incur performance costs for obscure units: allow users to specify minimal sets of things for common workflows
 - Don't incur performance costs for nicer APIs (e.g. string processing, output to notebooks, etc)
 - Quantity and Unit classes are numbers and should be as transparent/minimal as possible, holding as few external references as possible, and should be serialisable with as little pain as possible


## Road Map

 - Unified unit types (currently there are three);
 - A parser for text representations of units
 - Much better test pack
 - Benchmarks
 - Compilation to C


Operators to support

    op1 = (operator.neg, operator.truth)
    op2_cmp = (operator.eq,)  # operator.lt)
    op2_math = (operator.add, operator.sub, operator.mul, operator.truediv)



Base units

    #### BASE UNITS ####

    meter = [length] = m = metre
    second = [time] = s = sec
    ampere = [current] = A = amp
    candela = [luminosity] = cd = candle
    gram = [mass] = g
    mole = [substance] = mol
    kelvin = [temperature]; offset: 0 = K = degK = °K = degree_Kelvin = degreeK  # older names supported for compatibility
    radian = [] = rad
    bit = []
    count = []

