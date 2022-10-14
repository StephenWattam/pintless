

Things this doesn't support:

 - unit groups: use a new definition file if you want this.
 - Units that don't scale from 0, e.g. degrees C and F.




Operators to support

    op1 = (operator.neg, operator.truth)
    op2_cmp = (operator.eq,)  # operator.lt)
    op2_math = (operator.add, operator.sub, operator.mul, operator.truediv)



Prefixes to add:

        # binary_prefixes
        kibi- = 2**10
         = Ki-
        mebi- = 2**20
         = Mi-
        gibi- = 2**30
         = Gi-
        tebi- = 2**40
         = Ti-
        pebi- = 2**50
         = Pi-
        exbi- = 2**60
         = Ei-
        zebi- = 2**70
         = Zi-
        yobi- = 2**80
         = Yi-

        # extra_prefixes
        semi- = 0.5
         = _ = demi-
        sesqui- = 1.5




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

