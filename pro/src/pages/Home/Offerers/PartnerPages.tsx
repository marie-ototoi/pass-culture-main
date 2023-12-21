import React, { useState } from 'react'

import { GetOffererVenueResponseModel } from 'apiClient/v1'
import { SelectOption } from 'custom_types/form'
import SelectInput from 'ui-kit/form/Select/SelectInput'
import { FieldLayout } from 'ui-kit/form/shared'

import styles from './PartnerPages.module.scss'

export interface PartnerPagesProps {
  venues: GetOffererVenueResponseModel[]
}

export const PartnerPages = ({ venues }: PartnerPagesProps) => {
  const venuesOptions: SelectOption[] = venues.map((venue) => ({
    label: venue.name,
    value: venue.id.toString(),
  }))
  const [selectedVenue, setSelectedVenue] = useState<string>(
    venues.length > 0 ? venues[0].id.toString() : ''
  )

  return (
    <section className={styles['section']}>
      <h3 className={styles['title']}>
        {venues.length === 1 ? 'Votre page partenaire' : 'Vos pages partenaire'}
      </h3>

      <p className={styles['description']}>
        Complétez vos informations pour présenter votre activité au grand public
        sur le site et l’application pass Culture à destination des jeunes et /
        ou auprès des enseignants sur la plateforme Adage.
      </p>

      {venues.length > 1 && (
        <>
          <FieldLayout label="Sélectionnez votre page partenaire" name="venues">
            <SelectInput
              name="venues"
              options={venuesOptions}
              value={selectedVenue}
              onChange={(e) => setSelectedVenue(e.target.value)}
            />
          </FieldLayout>
        </>
      )}
    </section>
  )
}
