import {
  useField,
} from 'formik'
import React, { useEffect } from 'react'
import { humanizeSiren, unhumanizeSiren } from 'core/Offerers/utils'

import TextInput from '../TextInput'

const formatSiren = (value: string) => {
  // remove character when when it's not a number
  // this way we're sure that this field only accept number
  if (value && isNaN(Number(value))) {
    return value.slice(0, -1)
  }
  return humanizeSiren(value)
}

interface ISirenInputProps {
  label: string
  name?: string
  placeholder?: string
  form_callback: (value: string) => void
}

const SirenInput = ({
  label,
  name = 'siren',
  placeholder = '123456789',
  form_callback,
}: ISirenInputProps): JSX.Element => {
  const [field, meta, helpers] = useField({ name })
  const { setValue } = helpers;
  useEffect(() => {
    if (!meta.touched) return
    if (!meta.error) {
      setValue(formatSiren(field.value))
      form_callback(field.value)
    }
  }, [meta.touched, meta.error])

  return (
    <TextInput
      label={label}
      maxLength={11}
      name={name}
      placeholder={placeholder}
      type="text"
    />
  )
}

export default SirenInput
