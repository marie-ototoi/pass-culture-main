import { action } from '@storybook/addon-actions'
import { Formik } from 'formik'
import React from 'react'

import PasswordInput from './PasswordInput'

export default {
  title: 'ui-kit/forms/PasswordInput',
  component: PasswordInput,
}

const Template = () => (

  <Formik
    initialValues={{ siren: '' }}
    onSubmit={action('onSubmit')}
  >
    {({ getFieldProps }) => {

      return (
        <PasswordInput
          label="password"
          placeholder='Mon mot de passe'
          {...getFieldProps('password')}
        />
      )
    }}
  </Formik >
)

export const Default = Template.bind({})
