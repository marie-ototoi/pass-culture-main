import { Form, FormikProvider, useFormik } from 'formik'
import React, { useEffect } from 'react'
import { useDispatch } from 'react-redux'
import { useHistory, useLocation } from 'react-router-dom'
import * as yup from 'yup'

import useCurrentUser from 'components/hooks/useCurrentUser'
import useNotification from 'components/hooks/useNotification'
import LegalInfos from 'components/layout/LegalInfos/LegalInfos'
import { redirectLoggedUser } from 'components/router/helpers'
import { BannerRGS } from 'new_components/Banner'
import * as pcapi from 'repository/pcapi/pcapi'
import { removeErrors } from 'store/reducers/errors'
import { Button, SubmitButton, TextInput } from 'ui-kit'
import { Checkbox } from 'ui-kit'
import { ButtonVariant } from 'ui-kit/Button/types'
import { removeWhitespaces } from 'utils/string'

import OperatingProcedures from './OperationProcedures'
import SirenInput from 'ui-kit/form/SirenInput'
import { getSirenDataAdapter } from 'core/Offerers/adapters'
import PasswordInput from 'ui-kit/form/PasswordInput'

const STATE_ERROR_NAME = 'user'

const validationSchema = yup.object().shape({
  email: yup
    .string()
    .max(120)
    .email('Veuillez renseigner un email valide')
    .required('Veuillez renseigner un email'),
  password: yup
    .string()
    .required('Veuillez renseigner un mot de passe')
    .min(12, 'Votre mot de passe doit contenir au moins 12 caractères')
    .test(
      'isPasswordValid',
      'Votre mot de passe a un format invalide',
      value => {
        if (!value) return false
        const hasUpperCase = /[A-Z]/.test(value)
        const hasLowerCase = /[a-z]/.test(value)
        const hasNumber = /[0-9]/.test(value)
        const hasSymbole = /[!"#$%&'()*+,-./:;<=>?@[\\^_`{|}~\]]/.test(value)
        if (hasUpperCase && hasLowerCase && hasNumber && hasSymbole) {
          return true
        }
        return false
      }
    ),
  lastName: yup.string().max(128).required('Veuillez renseigner votre nom'),
  firstName: yup.string().max(128).required('Veuillez renseigner votre prénom'),
  phoneNumber: yup
    .string()
    .min(10, 'Veuillez renseigner au moins 10 chiffres')
    .max(20, 'Veuillez renseigner moins de 20 chiffres')
    .required('Veuillez renseigner votre numéro de télphone'),
  contactOk: yup.string(),
  siren: yup
    .string()
    .required('Veuillez rensigner le siren de votre entreprise')
    .min(9, 'Veuillez saisir 9 chiffres')
    .max(11, 'Veuillez saisir 9 chiffres')
  ,
})

interface ISignupFormFields {
  email: string
  password: string
  firstName: string
  lastName: string
  phoneNumber: string
  contactOk: string
  siren: string
}

interface ISignupFields extends ISignupFormFields {
  legalUnitValues: {
    address: string
    city: string
    latitude: string | null
    longitude: string | null
    name: string
    postalCode: string
    siren: string
  }
}

interface ISignupApiResponse extends ISignupFormFields {
  address: string
  city: string
  latitude: string | null
  longitude: string | null
  name: string
  postalCode: string
}

const SignupForm = (): JSX.Element => {
  const history = useHistory()
  const dispatch = useDispatch()
  const notification = useNotification()
  const { currentUser } = useCurrentUser()
  const location = useLocation()

  useEffect(() => {
    redirectLoggedUser(history, location, currentUser)
  }, [currentUser])

  useEffect(() => {
    const script = document.createElement('script')

    script.src = '//js.hs-scripts.com/5119289.js'
    script.async = true
    script.type = 'text/javascript'
    script.id = 'hs-script-loader'
    script.defer = true

    document.body.appendChild(script)
    return () => {
      const script = document.getElementById('hs-script-loader') as Node
      document.body.removeChild(script)
    }
  }, [])


  const initialValues = {
    email: '',
    password: '',
    lastName: '',
    firstName: '',
    phoneNumber: '',
    contactOk: '',
    siren: '',
    legalUnitValues: {
      address: '',
      city: '',
      latitude: null,
      longitude: null,
      name: '',
      postalCode: '',
      siren: '',
    },
  }

  const onSubmit = (values: ISignupFields) => {
    dispatch(removeErrors(STATE_ERROR_NAME))
    const { legalUnitValues, ...flattenvalues } = values
    const { firstName, siren } = flattenvalues
    pcapi
      .signup({
        ...flattenvalues,
        ...legalUnitValues,
        siren: removeWhitespaces(siren),
        publicName: firstName,
      })
      .then(() => onHandleSuccess())
      .catch(response => onHandleFail(response.errors ? response.errors : {}))
  }

  const onHandleSuccess = () => {
    history.replace('/inscription/confirmation')
  }

  const onHandleFail = (errors: ISignupApiResponse) => {
    for (let field in errors)
      formik.setFieldError(field, (errors as any)[field])

    if (errors) formik.setErrors(errors)
    notification.error(
      'Une ou plusieurs erreurs sont présentes dans le formulaire.'
    )
  }

  const { resetForm, ...formik } = useFormik({
    initialValues,
    onSubmit: onSubmit,
    validationSchema,
    validateOnChange: false,
  })

  const getSirenAPIData = async (siren: string) => {
    const response = await getSirenDataAdapter(siren)
    if (response.isOk)
      formik.setFieldValue('legalUnitValues', response.payload.values)
    else formik.setFieldError('siren', response.message)
  }

  return (
    <section className="sign-up-form-page">
      <div className="content">
        <h1>Créer votre compte professionnel</h1>
        <h2>Merci de compléter les champs suivants pour créer votre compte.</h2>
        <OperatingProcedures />

        <div className="sign-up-tips">
          Tous les champs sont obligatoires sauf mention contraire
        </div>
        <FormikProvider value={{ ...formik, resetForm }}>
          <Form onSubmit={formik.handleSubmit}>
            <div className="sign-up-form">
              <TextInput
                label="Adresse e-mail"
                name="email"
                placeholder="nom@example.fr"
              />
              <PasswordInput
                name="password"
                label="Mot de passe"
                placeholder="Mon mot de passe"
              />
              <TextInput label="Nom" name="lastName" placeholder="Mon nom" />
              <TextInput
                label="Prénom"
                name="firstName"
                placeholder="Mon prénom"
              />
              <TextInput
                label="Téléphone (utilisé uniquement par l’équipe du pass Culture)"
                name="phoneNumber"
                placeholder="Mon numéro de téléphone"
              />
              <div className="siren-field">
                <SirenInput
                  label="SIREN de la structure que vous représentez"
                  form_callback={getSirenAPIData}
                />
                <span className="field-siren-value">
                  {formik.values.legalUnitValues.name}
                </span>
              </div>
              <Checkbox
                hideFooter
                label="J’accepte d’être contacté par e-mail pour recevoir les
                      nouveautés du pass Culture et contribuer à son
                      amélioration (facultatif)"
                name="contactOk"
                value={formik.values.contactOk}
              />
              <LegalInfos
                className="sign-up-infos-before-signup"
                title="Créer mon compte"
              />
              <BannerRGS />
            </div>
            <div className="buttons-field">
              <Button
                onClick={() => history.push('/connexion')}
                variant={ButtonVariant.SECONDARY}
              >
                J’ai déjà un compte
              </Button>
              <SubmitButton className="primary-button" isLoading={formik.isSubmitting} disabled={!formik.dirty || !formik.isValid}>
                Créer mon compte
              </SubmitButton>
            </div>
          </Form>
        </FormikProvider>
      </div>
    </section>
  )
}

export default SignupForm
