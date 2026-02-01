from enum import Enum

class CallOutcomeA(Enum):
    CALLBACK = "CALLBACK"

class CallOutcomeB(str, Enum):
    CALLBACK = "CALLBACK"

outcome_from_analysis = CallOutcomeB.CALLBACK
outcome_expected = CallOutcomeA.CALLBACK

print(f"Outcome from analysis type: {type(outcome_from_analysis)}")
print(f"Outcome expected type: {type(outcome_expected)}")
print(f"Values match? {outcome_from_analysis.value == outcome_expected.value}")
print(f"Enums equal? {outcome_from_analysis == outcome_expected}")

if outcome_from_analysis == outcome_expected:
    print("MATCH")
else:
    print("NO MATCH")
