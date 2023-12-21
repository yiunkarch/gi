import itertools

class Evaluable:
    def __init__(self, eval, name=""):
        self.eval = eval
        self.name = name
    def __repr__(self):
        return "{{{}}}".format(self.name)
    def eval(self, c):
        raise NotImplemented
    @classmethod # TryEVal
    def tryEv(cls, c, x):
        return x.eval(c) if isinstance(x, Evaluable) else x
    # any -> Condition
    def __eq__(self, other):
        return Condition(lambda c: self.eval(c) == Evaluable.tryEv(c,other), name="{} == {}".format(self,other))
    def __gt__(self, other):
        return Condition(lambda c: self.eval(c) > Evaluable.tryEv(c,other), name="{} > {}".format(self,other))
    def __ge__(self, other):
        return Condition(lambda c: self.eval(c) >= Evaluable.tryEv(c,other), name="{} >= {}".format(self,other))
    def __lt__(self, other):
        return Condition(lambda c: self.eval(c) < Evaluable.tryEv(c,other), name="{} < {}".format(self,other))
    def __le__(self, other):
        return Condition(lambda c: self.eval(c) <= Evaluable.tryEv(c,other), name="{} <= {}".format(self,other))
    # any -> Evaluable
    def __add__(self, other):
        return Evaluable(lambda c: self.eval(c) + Evaluable.tryEv(c,other), name="{} + {}".format(self,other))
    def __radd__(self, other):
        return self.__add__(other)
    def __sub__(self, other):
        return Evaluable(lambda c: self.eval(c) - Evaluable.tryEv(c,other), name="{} - {}".format(self,other))
    def __rsub__(self, other):
        return Evaluable(lambda c: Evaluable.tryEv(c,other) - self.eval(c), name="{} - {}".format(other,self))
    def __mul__(self, other):
        return Evaluable(lambda c: self.eval(c) * Evaluable.tryEv(c,other), name="{} * {}".format(self,other))
    def __rmul__(self, other):
        return self.__mul__(other)
    def __truediv__(self, other):
        return Evaluable(lambda c: self.eval(c) / Evaluable.tryEv(c,other), name="{} / {}".format(self,other))
    def __rtruediv__(self, other):
        return Evaluable(lambda c: Evaluable.tryEv(c,other) / self.eval(c), name="{} / {}".format(other,self))
    def __lshift__(self, other):
        return Evaluable(lambda c: min(self.eval(c), Evaluable.tryEv(c,other)), name="{} << {}".format(self,other))
    def __rlshift__(self, other):
        return self.__lshift__(other)
    def __rshift__(self, other):
        return Evaluable(lambda c: max(self.eval(c), Evaluable.tryEv(c,other)), name="{} >> {}".format(self,other))
    def __rrshift__(self, other):
        return self.__rshift__(other)

class Profile:
    def __init__(self, data):
        self.data = {}
        for k,v in data.items():
            if isinstance(k, ConditionalField):
                v = k.makeEvaluable(v)
                k = k.field
            if not isinstance(k, Field):
                raise Exception
            if k not in self.data: self.data[k] = []
            self.data[k].append(v)
    def gi(self,k):
        if k not in self.data: return k.zero
        return list(map(lambda x: Evaluable.tryEv(self, x), self.data[k]))
    def __getitem__(self, k):
        if k not in self.data: return k.zero
        return k.combinator(map(lambda x: Evaluable.tryEv(self, x), self.data[k]))
    def __add__(self, other):
        p = Profile({})
        for k,v in itertools.chain(self.data.items(), other.data.items()):
            if k not in p.data: p.data[k] = []
            p.data[k] += v
        return p
    def overlay(self, other):
        p = Profile({})
        for k,v in itertools.chain(other.data.items(), self.data.items()):
            if k in p.data: continue
            p.data[k] = v
        return p
    
class Field(Evaluable):
    def __init__(self, name, zero=0, combinator=sum):
        super().__init__(lambda c: c[self])
        self.name = name
        self.zero = zero
        self.combinator = combinator
    def __repr__(self):
        return "<{}>".format(self.name)
    def __hash__(self):
        return hash(self.name)
    # callable -> ConditionalField
    def __getitem__(self, key):
        if isinstance(key, Condition):
            return ConditionalField(self, key)
        raise Exception

class Condition:
    def __init__(self, check, name=""):
        self.check = check
        self.name = name
    def __repr__(self):
        return "if({})".format(self.name)
    def check():
        raise NotImplemented
    def __hash__(self):
        return hash(self.check)
    def __and__(self, other):
        return Condition(lambda c: self.check(c) and other.check(c), name="({}) and ({})".format(self.name, other.name))
    def __or__(self, other):
        return ConditionalField(
            self.field,
            lambda c: self.check(c) and other.check(c))

class ConditionalField:
    def __init__(self, field, condition):
        self.field = field
        self.condition = condition
    def __repr__(self):
        return "<{} {}>".format(self.field, self.condition)
    def __hash__(self):
        return hash(self.field) ^ hash(self.condition)
    def makeEvaluable(self, v):
        return Evaluable(lambda c: Evaluable.tryEv(c, v if self.condition.check(c) else self.field.zero), name="{} {}".format(v, self.condition))