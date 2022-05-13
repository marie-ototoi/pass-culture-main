import '@testing-library/jest-dom'

import * as pcapi from 'repository/pcapi/pcapi'

import { MemoryRouter, Route } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'

import { Provider } from 'react-redux'
import React from 'react'
import VenueCreation from '../VenueCreation'
import VenueType from '../../ValueObjects/VenueType'
import { configureTestStore } from 'store/testUtils'
import { setVenueValues } from './helpers'
import userEvent from '@testing-library/user-event'

jest.mock('repository/pcapi/pcapi')

jest.mock(
  'components/pages/Offerers/Offerer/VenueV1/fields/LocationFields/utils/fetchAddressData.js',
  () => ({
    __esModule: true,
    default: jest.fn(),
  })
)

const renderVenueCreation = async ({ props, storeOverrides = {} }) => {
  const store = configureTestStore(storeOverrides)
  const rtlReturns = render(
    <Provider store={store}>
      <MemoryRouter initialEntries={['/structure/BQ/lieux/creation']}>
        <Route path="/structure/:offererId/lieux/creation">
          <VenueCreation {...props} />
        </Route>
        <Route path="/accueil">Bienvenue sur l'accueil</Route>
      </MemoryRouter>
    </Provider>
  )

  await screen.findByText('Informations lieu', { selector: 'h2' })

  return rtlReturns
}

describe('venue form', () => {
  let push
  let props
  let storeOverrides = {
    data: {
      users: [
        { publicName: 'René', isAdmin: false, email: 'rené@example.com' },
      ],
    },
  }

  beforeEach(() => {
    push = jest.fn()
    props = {
      formInitialValues: {
        id: 'CM',
      },
      history: {
        location: {
          pathname: '/fake',
        },
        push: push,
      },
      isEntrepriseApiDisabled: false,
      isBankInformationWithSiretActive: true,
      params: {
        offererId: 'APEQ',
        venueId: 'AQYQ',
      },
    }
    pcapi.getOfferer.mockResolvedValue({
      id: 'BQ',
      name: 'Maison du chocolat',
    })
    pcapi.getVenueTypes.mockResolvedValue([
      new VenueType({
        id: 'VISUAL_ARTS',
        label: 'Arts visuels, arts plastiques et galeries',
      }),
    ])
    pcapi.getVenueLabels.mockResolvedValue([])
    pcapi.getBusinessUnits.mockResolvedValue([])
  })

  describe('when submiting a valide form', () => {
    let formValues
    let submitButton
    let testId = 0

    beforeEach(async () => {
      // calls external api are saved with cacheSelector.
      // in order to get a new call each time we need to change called argument.
      // FIXME: make cacheSelector reset on each test.
      testId += 1
      await renderVenueCreation({ props, storeOverrides })

      formValues = {
        name: 'Librairie de test',
        comment: 'Pas de siret',
        venueTypeCode: 'VISUAL_ARTS',
        address: `Addresse de test ${testId}`,
        city: 'Paris',
        postalCode: '75001',
        latitude: Number(`50.29222${testId}`),
        longitude: Number(`3.96999${testId}`),
        noDisabilityCompliant: true,
      }
      await setVenueValues(formValues)
      submitButton = await screen.findByRole('button', { name: 'Créer' })
    })

    it('should handle success response', async () => {
      pcapi.createVenue.mockResolvedValue({ id: 'fake_success_id' })
      userEvent.click(submitButton)
      await waitFor(() => {
        expect(submitButton).toBeDisabled()
      })
      expect(pcapi.createVenue).toHaveBeenCalledWith({
        address: formValues['address'],
        audioDisabilityCompliant: false,
        bookingEmail: 'rené@example.com',
        city: formValues['city'],
        comment: formValues['comment'],
        description: '',
        latitude: formValues['latitude'],
        longitude: formValues['longitude'],
        managingOffererId: 'BQ',
        mentalDisabilityCompliant: false,
        motorDisabilityCompliant: false,
        name: formValues['name'],
        postalCode: formValues['postalCode'],
        venueLabelId: null,
        venueTypeCode: formValues['venueTypeCode'],
        visualDisabilityCompliant: false,
      })
      await expect(
        screen.findByText("Bienvenue sur l'accueil")
      ).resolves.toBeInTheDocument()
    })

    it('should handle error response', async () => {
      const errors = {
        name: ['error on name'],
      }
      pcapi.createVenue.mockRejectedValue({ errors })
      userEvent.click(submitButton)
      await waitFor(() => {
        expect(submitButton).toBeDisabled()
      })
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled()
        expect(pcapi.createVenue).toHaveBeenCalledWith({
          address: formValues['address'],
          audioDisabilityCompliant: false,
          bookingEmail: 'rené@example.com',
          city: formValues['city'],
          comment: formValues['comment'],
          description: '',
          latitude: formValues['latitude'],
          longitude: formValues['longitude'],
          managingOffererId: 'BQ',
          mentalDisabilityCompliant: false,
          motorDisabilityCompliant: false,
          name: formValues['name'],
          postalCode: formValues['postalCode'],
          venueLabelId: null,
          venueTypeCode: formValues['venueTypeCode'],
          visualDisabilityCompliant: false,
        })
        expect(screen.getByText(errors['name'])).toBeInTheDocument()
        expect(
          screen.queryByText("Bienvenue sur l'accueil")
        ).not.toBeInTheDocument()
      })
    })
  })

  it('should display proper title', async () => {
    props.match = {
      params: {
        offererId: 'APEQ',
        venueId: 'nouveau',
      },
    }
    await renderVenueCreation({ props, storeOverrides })
    await expect(
      screen.findByText('Ajoutez un lieu où accéder à vos offres.', {
        exact: false,
      })
    ).resolves.toBeInTheDocument()
  })

  it('should display contact fields', async () => {
    await renderVenueCreation({ props, storeOverrides })
    const contactPhoneNumber = await screen.findByLabelText('Téléphone :')
    const contactMail = await screen.findByLabelText('Mail :')
    const contactUrl = await screen.findByLabelText('URL de votre site web :')

    expect(contactPhoneNumber).toBeInTheDocument()
    expect(contactMail).toBeInTheDocument()
    expect(contactUrl).toBeInTheDocument()

    expect(contactPhoneNumber).toBeEnabled()
    expect(contactMail).toBeEnabled()
    expect(contactUrl).toBeEnabled()
  })

  it('should fill contact fields', async () => {
    await renderVenueCreation({ props, storeOverrides })
    const contactPhoneNumber = await screen.findByLabelText('Téléphone :')
    const contactMail = await screen.findByLabelText('Mail :')
    const contactUrl = await screen.findByLabelText('URL de votre site web :')

    userEvent.paste(contactPhoneNumber, '0606060606')
    userEvent.paste(contactMail, 'test@test.com')
    userEvent.paste(contactUrl, 'https://some-url-test.com')
    waitFor(() => {
      expect(contactUrl).toHaveValue('https://some-url-test.com')
      expect(contactPhoneNumber).toHaveValue('0606060606')
      expect(contactMail).toHaveValue('test@test.com')
    })
  })

  describe('business unit fileds', () => {
    storeOverrides = {
      ...storeOverrides,
      features: {
        list: [
          {
            nameKey: 'ENFORCE_BANK_INFORMATION_WITH_SIRET',
            isActive: true,
          },
        ],
      },
    }
    beforeEach(() => {
      pcapi.getBusinessUnits.mockResolvedValue([
        {
          id: 20,
          iban: 'FR0000000000000002',
          name: 'Business unit #1',
          siret: '22222222311111',
        },
        {
          id: 21,
          iban: 'FR0000000000000003',
          name: 'Business unit #2',
          siret: '22222222311222',
        },
      ])
    })

    it('should display business unit select list when structure have business units', async () => {
      // Given
      await renderVenueCreation({ props, storeOverrides })

      // Then
      await expect(
        screen.findByLabelText(
          'Coordonnées bancaires pour vos remboursements :'
        )
      ).resolves.toBeInTheDocument()
    })

    it('should not display business unit select list when structure does not have busiess units', async () => {
      // Given
      pcapi.getBusinessUnits.mockResolvedValue([])

      // When
      await renderVenueCreation({ props, storeOverrides })

      // Then
      await expect(
        screen.queryByLabelText(
          'Coordonnées bancaires pour vos remboursements :'
        )
      ).not.toBeInTheDocument()
    })
  })
})
