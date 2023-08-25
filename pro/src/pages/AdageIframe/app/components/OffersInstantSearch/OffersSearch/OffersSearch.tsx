import './OldOffersSearch.scss'

import { FormikContext, useFormik } from 'formik'
import { useContext, useEffect, useRef, useState } from 'react'
import * as React from 'react'
import type { SearchBoxProvided } from 'react-instantsearch-core'
import { connectSearchBox } from 'react-instantsearch-dom'

import { VenueResponse } from 'apiClient/adage'
import { apiAdage } from 'apiClient/api'
import useActiveFeature from 'hooks/useActiveFeature'
import useIsElementVisible from 'hooks/useIsElementVisible'
import strokeOffersIcon from 'icons/stroke-offers.svg'
import strokeVenueIcon from 'icons/stroke-venue.svg'
import useAdageUser from 'pages/AdageIframe/app/hooks/useAdageUser'
import {
  FacetFiltersContext,
  FiltersContext,
} from 'pages/AdageIframe/app/providers'
import Tabs from 'ui-kit/Tabs'
import { removeParamsFromUrl } from 'utils/removeParamsFromUrl'

import { GeoLocation } from '../OffersInstantSearch'
import {
  ADAGE_FILTERS_DEFAULT_VALUES,
  adageFiltersToFacetFilters,
  computeFiltersInitialValues,
  populateFacetFilters,
} from '../utils'

import { OfferFilters } from './OfferFilters/OfferFilters'
import { Offers } from './Offers/Offers'

export enum LocalisationFilterStates {
  DEPARTMENTS = 'departments',
  ACADEMIES = 'academies',
  GEOLOCATION = 'geolocation',
  NONE = 'none',
}

export interface SearchProps extends SearchBoxProvided {
  venueFilter: VenueResponse | null
  setGeoLocation: (geoloc: GeoLocation) => void
}

export interface SearchFormValues {
  query: string
  domains: string[]
  students: string[]
  departments: string[]
  academies: string[]
  eventAddressType: string
  categories: string[][]
  geolocRadius: number
}

enum OfferTab {
  ALL = 'all',
  ASSOCIATED_TO_INSTITUTION = 'associatedToInstitution',
}

export const OffersSearchComponent = ({
  venueFilter,
  setGeoLocation,
  refine,
}: SearchProps): JSX.Element => {
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [activeTab, setActiveTab] = useState(OfferTab.ALL)

  const { dispatchCurrentFilters, currentFilters } = useContext(FiltersContext)
  const { setFacetFilters } = useContext(FacetFiltersContext)
  const adageUser = useAdageUser()
  const userUAICode = adageUser.uai
  const uaiCodeAllInstitutionsTab = userUAICode ? ['all', userUAICode] : ['all']
  const uaiCodeShareWithMyInstitutionTab = userUAICode ? [userUAICode] : null

  const handleTabChange = (tab: OfferTab) => {
    dispatchCurrentFilters({
      type: 'RESET_CURRENT_FILTERS',
    })
    setActiveTab(tab)
    setFacetFilters(
      populateFacetFilters({
        ...currentFilters,
        venueFilter,
        uai:
          tab === OfferTab.ASSOCIATED_TO_INSTITUTION
            ? uaiCodeShareWithMyInstitutionTab
            : uaiCodeAllInstitutionsTab,
      }).queryFilters
    )
  }

  const tabs = [
    {
      label: 'Toutes les offres',
      key: OfferTab.ALL,
      onClick: () => handleTabChange(OfferTab.ALL),
      icon: strokeOffersIcon,
    },
    {
      label: 'Partagé avec mon établissement',
      key: OfferTab.ASSOCIATED_TO_INSTITUTION,
      onClick: () => handleTabChange(OfferTab.ASSOCIATED_TO_INSTITUTION),
      icon: strokeVenueIcon,
    },
  ]

  const isNewHeaderActive = useActiveFeature('WIP_ENABLE_NEW_ADAGE_HEADER')

  const handleSubmit = () => {
    const updatedFilters = adageFiltersToFacetFilters({
      ...formik.values,
      uai:
        activeTab === OfferTab.ASSOCIATED_TO_INSTITUTION
          ? uaiCodeShareWithMyInstitutionTab
          : uaiCodeAllInstitutionsTab,
    })

    setFacetFilters(updatedFilters.queryFilters)

    setGeoLocation(
      localisationFilterState === LocalisationFilterStates.GEOLOCATION
        ? {
            radius: formik.values.geolocRadius * 1000,
            //  TODO: get the adage user institution position from ADAGE
            latLng: '48.864716, 2.349014',
          }
        : {}
    )
    refine(formik.values.query)
  }

  const resetForm = () => {
    setlocalisationFilterState(LocalisationFilterStates.NONE)
    formik.setValues(ADAGE_FILTERS_DEFAULT_VALUES)
    formik.handleSubmit()
  }

  const logFiltersOnSearch = (nbHits: number, queryId: string) => {
    /* istanbul ignore next: TO FIX the current structure make it hard to test, we probably should not mock Offers in OfferSearch tests */
    apiAdage.logTrackingFilter({
      iframeFrom: removeParamsFromUrl(location.pathname),
      resultNumber: nbHits,
      queryId: queryId,
      filterValues: formik ? formik.values : {},
    })
  }
  useEffect(() => {
    refine(venueFilter?.publicName || venueFilter?.name || '')
  }, [venueFilter])

  const formik = useFormik<SearchFormValues>({
    initialValues: computeFiltersInitialValues(
      adageUser.departmentCode,
      venueFilter
    ),
    enableReinitialize: true,
    onSubmit: handleSubmit,
  })
  const getActiveLocalisationFilter = () => {
    if (formik.values.departments.length > 0) {
      return LocalisationFilterStates.DEPARTMENTS
    }
    if (formik.values.academies.length > 0) {
      return LocalisationFilterStates.ACADEMIES
    }
    return LocalisationFilterStates.NONE
  }
  const [localisationFilterState, setlocalisationFilterState] =
    useState<LocalisationFilterStates>(getActiveLocalisationFilter())

  const offerFilterRef = useRef<HTMLDivElement>(null)
  const isOfferFiltersVisible = useIsElementVisible(offerFilterRef)

  return (
    <>
      <FormikContext.Provider value={formik}>
        {!!adageUser.uai && !isNewHeaderActive && (
          <Tabs selectedKey={activeTab} tabs={tabs} />
        )}
        <div ref={offerFilterRef}>
          <OfferFilters
            className="search-filters"
            isLoading={isLoading}
            localisationFilterState={localisationFilterState}
            setLocalisationFilterState={setlocalisationFilterState}
            resetForm={resetForm}
          />
        </div>
        <div className="search-results">
          <Offers
            setIsLoading={setIsLoading}
            resetForm={resetForm}
            logFiltersOnSearch={logFiltersOnSearch}
            submitCount={formik.submitCount}
            isBackToTopVisibile={!isOfferFiltersVisible}
          />
        </div>
      </FormikContext.Provider>
    </>
  )
}

export const OffersSearch = connectSearchBox<SearchProps>(OffersSearchComponent)
