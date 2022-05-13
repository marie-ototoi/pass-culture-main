import '@testing-library/jest-dom'

import { render, screen, waitFor } from '@testing-library/react'

import AppLayout from '../AppLayout'
import { MemoryRouter } from 'react-router'
import { Provider } from 'react-redux'
import React from 'react'
import { configureTestStore } from 'store/testUtils'

const renderApp = async (props, store, url = '/') => {
  render(
    <Provider store={store}>
      <MemoryRouter initialEntries={[url]}>
        <AppLayout {...props}>
          <p>Sub component</p>
        </AppLayout>
      </MemoryRouter>
    </Provider>
  )
}

describe('src | AppLayout', () => {
  let props
  let store

  beforeEach(() => {
    props = {}
    store = configureTestStore({
      data: { users: [{ publicName: 'François', isAdmin: false }] },
    })
  })

  it('should not render domain name banner when arriving from new domain name', async () => {
    // Given / When
    renderApp(props, store)

    // Then
    await waitFor(() =>
      expect(
        screen.queryByText(content =>
          content.startsWith('Notre nom de domaine évolue !')
        )
      ).not.toBeInTheDocument()
    )
  })

  it('should render domain name banner when coming from old domain name', async () => {
    // When
    renderApp(props, store, '/?redirect=true')

    // Then
    await waitFor(() =>
      expect(
        screen.queryByText(content =>
          content.startsWith('Notre nom de domaine évolue !')
        )
      ).toBeInTheDocument()
    )
  })
})
