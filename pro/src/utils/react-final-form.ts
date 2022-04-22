type TValidator = (value: string) => string | void
type TAsyncValidator = (value: string) => Promise<string | void>
type TComposeValidatorsReturn = (string | void) | Promise<string | void>

export const composeValidators =
  (...validators: (TValidator | TAsyncValidator | null | undefined)[]) =>
  (value: string): TComposeValidatorsReturn => {
    for (const i in validators) {
      const validator = validators[i]
      if (!validator) {
        continue
      }

      const error: TComposeValidatorsReturn = validator(value)
      if (error !== undefined) return error
    }
    return undefined
  }

export const createParseNumberValue =
  (type: 'number' | 'text') =>
  (value: number | string): string | number | null => {
    if (typeof value === undefined) {
      return null
    }
    if (type === 'text') {
      return value
    }

    let stringValue = String(value)
    if (stringValue === '') {
      return ''
    }
    if (stringValue.includes(',')) {
      stringValue = stringValue.replace(/,/g, '.')
    }

    return stringValue.includes('.')
      ? parseFloat(stringValue)
      : parseInt(stringValue, 10)
  }

export const createValidateRequiredField =
  (error: string, type?: 'text' | 'number') => (value: string) => {
    if (type === 'number' && value !== '') return undefined
    if (typeof value === 'string' && value !== '') return undefined
    return error
  }

export default createValidateRequiredField
