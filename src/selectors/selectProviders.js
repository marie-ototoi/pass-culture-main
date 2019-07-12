import { createSelector } from 'reselect'

const removedLocalClasses = [
  'OpenAgendaOffers',
  'SpreadsheetExpThingOffers',
  'SpreadsheetExpVenues',
  'SpreadsheetExpOffers',
  'SpreadsheetOffers',
  'TiteLiveOffers',
  'TiteLiveVenues',
  'TiteLiveThings',
  'TiteLiveBookThumbs',
  'TiteLiveBookDescriptions',
]

const selectProviders = createSelector(
  state => state.data.providers,
  providers =>
    providers
      .filter(p => !removedLocalClasses.includes(p.localClass))
      .sort((p1, p2) => p1.localClass - p2.localClass)
)

export default selectProviders
