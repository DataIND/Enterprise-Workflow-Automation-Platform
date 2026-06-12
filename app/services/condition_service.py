class ConditionService:

    def validate(self, conditions, payload):

        for condition in conditions:

            actual_value = payload.get(condition.field)

            if condition.operator == "eq":

                if actual_value != condition.value:

                    return False

            elif condition.operator == "gt":

                if actual_value <= condition.value:

                    return False

            elif condition.operator == "lt":

                if actual_value >= condition.value:

                    return False

        return True
