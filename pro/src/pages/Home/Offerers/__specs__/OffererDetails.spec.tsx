import { screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import React from 'react'

import * as useAnalytics from 'hooks/useAnalytics'
import { defaultGetOffererResponseModel } from 'utils/apiFactories'
import { renderWithProviders } from 'utils/renderWithProviders'

import { OffererDetails, OffererDetailsProps } from '../OffererDetails'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => ({
  ...((await vi.importActual('react-router-dom')) ?? {}),
  useNavigate: () => mockNavigate,
}))

const renderOffererDetails = (props: Partial<OffererDetailsProps> = {}) => {
  renderWithProviders(
    <OffererDetails
      isUserOffererValidated={true}
      offererOptions={[
        {
          value: defaultGetOffererResponseModel.id,
          label: defaultGetOffererResponseModel.name,
        },
      ]}
      selectedOfferer={defaultGetOffererResponseModel}
      {...props}
    />
  )
}

const mockLogEvent = vi.fn()

describe('OffererDetails', () => {
  beforeEach(() => {
    vi.spyOn(useAnalytics, 'default').mockImplementation(() => ({
      logEvent: mockLogEvent,
    }))
  })

  it('should display offerer select', () => {
    renderOffererDetails({ selectedOfferer: defaultGetOffererResponseModel })

    expect(
      screen.getByText(defaultGetOffererResponseModel.name)
    ).toBeInTheDocument()
  })

  it('should trigger an event when clicking on "Inviter" for offerers', async () => {
    renderOffererDetails()

    await userEvent.click(screen.getByText('Inviter'))

    expect(mockLogEvent).toHaveBeenCalledWith('hasClickedInviteCollaborator', {
      offererId: defaultGetOffererResponseModel.id,
    })
    expect(mockLogEvent).toHaveBeenCalledTimes(1)
  })

  it('should trigger an event when clicking on "Modifier" for offerers', async () => {
    renderOffererDetails()

    await userEvent.click(screen.getByText('Modifier'))

    expect(mockLogEvent).toHaveBeenCalledWith('hasClickedModifyOfferer', {
      offerer_id: defaultGetOffererResponseModel.id,
    })
    expect(mockLogEvent).toHaveBeenCalledTimes(1)
  })

  it('should not allow user to update offerer informations when user attachment to offerer is not yet validated', () => {
    renderOffererDetails({ isUserOffererValidated: false })

    const offererUpdateButton = screen.getByText('Modifier')
    expect(offererUpdateButton).toBeInTheDocument()
    expect(offererUpdateButton).toHaveAttribute('aria-disabled')
  })

  it('should redirect to offerer creation page when selecting "add offerer" option"', async () => {
    renderOffererDetails()

    await userEvent.selectOptions(
      screen.getByLabelText('Structure'),
      '+ Ajouter une structure'
    )

    expect(mockNavigate).toHaveBeenCalledWith('/structures/creation')
  })
})
