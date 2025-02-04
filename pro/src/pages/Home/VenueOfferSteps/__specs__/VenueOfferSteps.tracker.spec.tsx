import { screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import React from 'react'

import {
  defaultGetOffererResponseModel,
  defaultGetOffererVenueResponseModel,
} from 'utils/apiFactories'
import {
  RenderWithProvidersOptions,
  renderWithProviders,
} from 'utils/renderWithProviders'

import { Events, VenueEvents } from '../../../../core/FirebaseEvents/constants'
import * as useAnalytics from '../../../../hooks/useAnalytics'
import * as venueUtils from '../../venueUtils'
import { VenueOfferSteps, VenueOfferStepsProps } from '../VenueOfferSteps'

const mockLogEvent = vi.fn()

const renderVenueOfferSteps = (
  props?: Partial<VenueOfferStepsProps>,
  options?: RenderWithProvidersOptions
) => {
  return renderWithProviders(
    <VenueOfferSteps
      hasVenue={false}
      offerer={{
        ...defaultGetOffererResponseModel,
        hasPendingBankAccount: false,
        hasValidBankAccount: false,
        hasNonFreeOffer: false,
      }}
      {...props}
    />,
    { initialRouterEntries: ['/accueil'], ...options }
  )
}

describe('VenueOfferSteps', () => {
  const venueId = 1
  const venue = {
    ...defaultGetOffererVenueResponseModel,
    id: venueId,
  }

  beforeEach(() => {
    vi.spyOn(useAnalytics, 'default').mockImplementation(() => ({
      logEvent: mockLogEvent,
    }))
    vi.spyOn(
      venueUtils,
      'shouldDisplayEACInformationSectionForVenue'
    ).mockReturnValue(true)
  })

  it('should track creation venue', async () => {
    renderVenueOfferSteps()

    await userEvent.click(screen.getByText(/Créer un lieu/))

    expect(mockLogEvent).toHaveBeenCalledTimes(1)
    expect(mockLogEvent).toHaveBeenNthCalledWith(
      1,
      Events.CLICKED_CREATE_VENUE,
      {
        from: '/',
        is_first_venue: true,
      }
    )
  })

  it('should track creation offer', async () => {
    renderVenueOfferSteps({ venue, hasVenue: true })

    await userEvent.click(screen.getByText(/Créer une offre/))
  })

  it('should track ReimbursementPoint', async () => {
    renderVenueOfferSteps({
      venue: { ...venue, hasMissingReimbursementPoint: true },
      hasVenue: true,
    })

    await userEvent.click(
      screen.getByText(/Renseigner des coordonnées bancaires/)
    )

    expect(mockLogEvent).toHaveBeenCalledTimes(1)
    expect(mockLogEvent).toHaveBeenCalledWith(
      VenueEvents.CLICKED_VENUE_ADD_RIB_BUTTON,
      {
        venue_id: venueId,
        from: 'Home',
      }
    )
  })

  it('should track ReimbursementPoint', async () => {
    renderVenueOfferSteps(
      {
        venue: { ...venue, hasMissingReimbursementPoint: false },
        hasVenue: true,
      },
      { features: ['WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY'] }
    )

    await userEvent.click(screen.getByText(/Ajouter un compte bancaire/))

    expect(mockLogEvent).toHaveBeenCalledTimes(1)
    expect(mockLogEvent).toHaveBeenCalledWith(
      VenueEvents.CLICKED_VENUE_ADD_RIB_BUTTON,
      {
        venue_id: venueId,
        from: 'Home',
      }
    )
  })

  it('should track "I have no venue"', async () => {
    renderVenueOfferSteps()

    await userEvent.click(
      screen.getByText(
        /Je ne dispose pas de lieu propre, quel type de lieu créer ?/
      )
    )

    expect(mockLogEvent).toHaveBeenCalledTimes(1)
    expect(mockLogEvent).toHaveBeenCalledWith(Events.CLICKED_NO_VENUE, {
      from: location.pathname,
    })
  })

  it('should track click on dms timeline link', async () => {
    renderVenueOfferSteps({
      venue: { ...venue, hasPendingBankInformationApplication: true },
      hasVenue: true,
    })

    await userEvent.click(
      screen.getByText('Suivre ma demande de référencement ADAGE')
    )

    expect(mockLogEvent).toHaveBeenCalledTimes(1)
    expect(mockLogEvent).toHaveBeenCalledWith(Events.CLICKED_EAC_DMS_TIMELINE, {
      from: location.pathname,
    })
  })

  it('should track click on dms redirect link', async () => {
    renderVenueOfferSteps({
      venue: {
        ...venue,
        hasPendingBankInformationApplication: true,
        hasMissingReimbursementPoint: false,
        demarchesSimplifieesApplicationId: 123456,
      },
    })

    await userEvent.click(
      screen.getByText('Suivre mon dossier de coordonnées bancaires')
    )

    expect(mockLogEvent).toHaveBeenCalledTimes(1)
    expect(mockLogEvent).toHaveBeenCalledWith(
      VenueEvents.CLICKED_BANK_DETAILS_RECORD_FOLLOW_UP,
      {
        from: location.pathname,
      }
    )
  })
})
