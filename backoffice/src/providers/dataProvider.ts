import { ExchangeInfo, Symbol } from 'binance-api-node'
import { DataProvider } from 'react-admin'

let assets: Symbol[] = []

export const dataProvider: DataProvider = {
  // @ts-ignore see later
  async getList(resource, params) {
    if (resource.includes('binance/api/v1')) {
      switch (resource) {
        default:
        case 'binance/api/v1/exchangeInfo':
          if (assets.length === 0) {
            const response = await fetch('https://api.binance.com/api/v1/exchangeInfo')
            const json: ExchangeInfo = await response.json()
            assets = json.symbols
              .map((item) => ({
                ...item,
                id: item.baseAsset,
              }))
            assets = assets
              .filter((obj, pos, arr) => arr.map(({ baseAsset }) => baseAsset).indexOf(obj.baseAsset) === pos)
          }

          return {
            data: assets,
            total: assets.length,
          }
      }
    }
    return {
      data: [],
      total: 0,
    }
  },
  // @ts-ignore
  async getOne(resource, params) {
    return {
      data: {
        id: 0,
      },
    }
  },
  async getMany(resource, params) {
    return {
      data: [],
      total: 0,
    }
  },
  async getManyReference(resource, params) {
    return {
      data: [],
      total: 0,
    }
  },
  // @ts-ignore
  async create(resource, params) {
    return {
      data: {
        id: 0,
      },
    }
  },
  // @ts-ignore
  async update(resource, params) {
    return {
      data: {
        id: 1,
      },
    }
  },
  async updateMany(resource, params) {
    return {
      data: [],
    }
  },
  // @ts-ignore
  async delete(resource, params) {
    return {
      data: {
        id: 1,
      },
    }
  },
  async deleteMany(resource, params) {
    return {
      data: [],
    }
  },
}
