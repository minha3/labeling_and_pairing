class ParameterError(Exception):
    pass


class ParameterKeyError(ParameterError):
    def __init__(self, key):
        super(ParameterKeyError, self).__init__(f'Missing required parameters: {key}')


class ParameterValueError(ParameterError):
    def __init__(self, key, value, should=None, choice=None):
        msg = f'Invalid value for {key}: "{value}".'
        if should:
            msg += f' Value should be "{should}"'
        elif choice:
            msg += f' choose from {choice}'
        super(ParameterValueError, self).__init__(msg)


class ParameterExistError(ParameterError):
    def __init__(self, value):
        super(ParameterExistError, self).__init__(f'{value} is already exist.')


class ParameterNotFoundError(ParameterError):
    def __init__(self, value):
        super(ParameterNotFoundError, self).__init__(f'{value} is not found.')


class ParameterEmptyError(ParameterError):
    def __init__(self, value):
        super(ParameterEmptyError, self).__init__(f'{value} is empty.')


class OperationError(Exception):
    pass
