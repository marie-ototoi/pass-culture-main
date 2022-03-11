import { useCallback, useMemo } from 'react'
import { useNavigate, useLocation } from 'react-router'

import {
  translateApiParamsToQueryParams,
  translateQueryParamsToApiParams,
} from 'utils/translate'

const useFrenchQuery = () => {
  const location = useLocation()
  const navigate = useNavigate()

  const frenchQueryParams = useMemo(
    () => Object.fromEntries(new URLSearchParams(location.search)),
    [location]
  )
  const englishQueryParams = useMemo(
    () => translateQueryParamsToApiParams(frenchQueryParams),
    [frenchQueryParams]
  )

  const setQuery = useCallback(
    newEnglishQueryParams => {
      const frenchQueryParams = translateApiParamsToQueryParams(
        newEnglishQueryParams
      )
      const frenchQueryString = new URLSearchParams(
        frenchQueryParams
      ).toString()
      navigate(`${location.pathname}?${frenchQueryString}`)
    },
    [navigate, location.pathname]
  )

  return [englishQueryParams, setQuery]
}

export default useFrenchQuery
