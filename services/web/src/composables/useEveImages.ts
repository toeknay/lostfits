/**
 * Composable for generating EVE image URLs from CCP's image server.
 *
 * Images are served from https://images.evetech.net/
 */
export function useEveImages() {
  const getShipRender = (typeId: number, size: 32 | 64 | 128 | 256 | 512 = 128) => {
    return `https://images.evetech.net/types/${typeId}/render?size=${size}`
  }

  const getItemIcon = (typeId: number, size: 32 | 64 | 128 | 256 = 64) => {
    return `https://images.evetech.net/types/${typeId}/icon?size=${size}`
  }

  return {
    getShipRender,
    getItemIcon
  }
}
