import { CollectiveStockResponseModel, StockResponse } from '../types'
import {
  DEFAULT_EAC_STOCK_FORM_VALUES,
  EducationalOfferType,
  GetStockOfferSuccessPayload,
  OfferEducationalStockFormValues,
} from 'core/OfferEducational'

import { getLocalDepartementDateTimeFromUtc } from 'utils/timezone'

export const extractInitialStockValues = (
  stock: StockResponse | CollectiveStockResponseModel | null,
  offer: GetStockOfferSuccessPayload
): OfferEducationalStockFormValues => {
  if (!stock) {
    return DEFAULT_EAC_STOCK_FORM_VALUES
  }

  return {
    eventDate:
      getLocalDepartementDateTimeFromUtc(
        stock.beginningDatetime,
        offer.venueDepartmentCode
      ) ?? DEFAULT_EAC_STOCK_FORM_VALUES.eventDate,
    eventTime:
      getLocalDepartementDateTimeFromUtc(
        stock.beginningDatetime,
        offer.venueDepartmentCode
      ) ?? DEFAULT_EAC_STOCK_FORM_VALUES.eventTime,
    numberOfPlaces:
      stock.numberOfTickets ?? DEFAULT_EAC_STOCK_FORM_VALUES.numberOfPlaces,
    totalPrice: stock.price,
    bookingLimitDatetime:
      getLocalDepartementDateTimeFromUtc(stock.bookingLimitDatetime) ??
      DEFAULT_EAC_STOCK_FORM_VALUES.bookingLimitDatetime,
    priceDetail:
      stock.educationalPriceDetail ?? DEFAULT_EAC_STOCK_FORM_VALUES.priceDetail,
    educationalOfferType: offer.isShowcase
      ? EducationalOfferType.SHOWCASE
      : EducationalOfferType.CLASSIC,
  }
}
