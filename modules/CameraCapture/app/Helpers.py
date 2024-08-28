class Helper:

    @classmethod
    def display_time_difference_in_ms(self, endTime, startTime):
        return str(int((endTime-startTime) * 1000)) + " ms"
    
    
    @classmethod
    def convert_string_to_bool(self, env):
        if env in ['True', 'TRUE', '1', 'y', 'YES', 'Y', 'Yes']:
            return True
        elif env in ['False', 'FALSE', '0', 'n', 'NO', 'N', 'No']:
            return False
        else:
            raise ValueError('Could not convert string to bool.')