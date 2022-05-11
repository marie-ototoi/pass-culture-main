import { action } from '@storybook/addon-actions'
import { Formik } from 'formik'
import React from 'react'

import SirenInput from './SirenInput'

export default {
  title: 'ui-kit/forms/SirenInput',
  component: SirenInput,
}
const formCb = (value: string) => {
  console.log("On valid field callback")
}

const Template = () => (
  <Formik initialValues={{ siren: '' }} onSubmit={action('onSubmit')}>
    {({ getFieldProps }) => {
      return (
        <SirenInput
          {...getFieldProps('siren')}
          label="Champ Siren"
          form_callback={formCb}
        />
      )
    }}
  </Formik>
)

export const Default = Template.bind({})
