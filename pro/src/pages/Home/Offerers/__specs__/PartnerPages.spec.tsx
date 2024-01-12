import { screen } from '@testing-library/react'
import React from 'react'
import * as router from 'react-router-dom'

import { VenueTypeCode } from 'apiClient/v1'
import {
  defaultGetOffererResponseModel,
  defaultGetOffererVenueResponseModel,
} from 'utils/apiFactories'
import { renderWithProviders } from 'utils/renderWithProviders'

import {
  PartnerPages,
  PartnerPagesProps,
  SAVED_VENUE_ID_KEY,
} from '../PartnerPages'

const renderPartnerPages = (props: Partial<PartnerPagesProps> = {}) => {
  renderWithProviders(
    <PartnerPages
      venues={[defaultGetOffererVenueResponseModel]}
      offerer={defaultGetOffererResponseModel}
      {...props}
    />
  )
}

vi.mock('react-router-dom', async () => ({
  ...((await vi.importActual('react-router-dom')) ?? {}),
  useLoaderData: vi.fn(),
}))

describe('PartnerPages', () => {
  beforeEach(() => {
    vi.spyOn(router, 'useLoaderData').mockReturnValue({
      venueTypes: [{ id: VenueTypeCode.FESTIVAL, label: 'Festival' }],
    })
  })

  it('should not display select if only one venue', () => {
    renderPartnerPages({
      venues: [
        {
          ...defaultGetOffererVenueResponseModel,
          venueTypeCode: VenueTypeCode.FESTIVAL,
        },
      ],
    })

    expect(
      screen.getByRole('heading', { name: 'Votre page partenaire' })
    ).toBeInTheDocument()
    expect(
      screen.queryByLabelText(/Sélectionnez votre page partenaire/)
    ).not.toBeInTheDocument()

    expect(screen.getByText('Festival')).toBeInTheDocument()
    expect(screen.getByText('Gérer ma page')).toBeInTheDocument()
  })

  it('should display select if multiple venues', () => {
    renderPartnerPages({
      venues: [
        defaultGetOffererVenueResponseModel,
        { ...defaultGetOffererVenueResponseModel, id: 1 },
      ],
    })

    expect(
      screen.getByRole('heading', { name: 'Vos pages partenaire' })
    ).toBeInTheDocument()
    expect(
      screen.queryByLabelText(/Sélectionnez votre page partenaire/)
    ).toBeInTheDocument()
  })

  it('should load saved venue in localStorage if no get parameter', () => {
    const selectedVenue = {
      ...defaultGetOffererVenueResponseModel,
      id: 666,
      name: 'super lieu',
    }
    localStorage.setItem(SAVED_VENUE_ID_KEY, selectedVenue.id.toString())

    renderPartnerPages({
      venues: [{ ...defaultGetOffererVenueResponseModel }, selectedVenue],
    })

    expect(screen.getAllByText('super lieu')[0]).toBeInTheDocument()
  })

  it('should not used saved venue in localStorage if it is not an option', () => {
    localStorage.setItem(SAVED_VENUE_ID_KEY, '123456')

    renderPartnerPages({ venues: [{ ...defaultGetOffererVenueResponseModel }] })

    expect(
      screen.getByText(defaultGetOffererVenueResponseModel.name)
    ).toBeInTheDocument()
  })
})
