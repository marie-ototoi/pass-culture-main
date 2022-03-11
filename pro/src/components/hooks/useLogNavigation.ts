// eslint-disable-next-line import/named
import { Location, LocationListener } from 'history'
import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router'

import useAnalytics from 'components/hooks/useAnalytics'

const useLogNavigation = (): LocationListener | void => {
  const analytics = useAnalytics()
  const navigate = useNavigate()
  const location = useLocation()
  useEffect(() => {
    const unlisten = navigate.listen((nextLocation: Location<unknown>) => {
      if (location.pathname !== nextLocation.pathname) {
        analytics.logPageView(nextLocation.pathname)
      }
    })
    return unlisten
  })
}

export default useLogNavigation
