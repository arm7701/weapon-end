# Shared desktop map runtime

This folder mirrors `weaponeering-backend/src/maap_app/ui/map/assets/` so the web app
uses the **same** Cesium map as the desktop program (`cesium_map.html`).

| File | Role |
| --- | --- |
| `cesium_map.html` | Desktop Cesium map (CDN Cesium 1.119 + Turf) |
| `borders/thailand_adm0_simplified.geojson` | Country border layer |
| `icons/airport.png` | Wing marker icon |

Vue loads it via iframe (`MapPanel.vue`) and drives layers through `window.maapMap`.

When updating the desktop map, copy the HTML here again (or sync both copies) and keep the small web patches:
- optional QWebChannel load
- `postMessage` for map events / MAP_READY
- hide Cesium credits
- `window.viewer` for detection screenshot capture
