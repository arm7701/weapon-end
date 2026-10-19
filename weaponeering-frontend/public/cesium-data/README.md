# Offline Cesium datasets

CesiumJS and its bundled Natural Earth imagery work offline without a token.

For higher-detail local data, place datasets under this directory and configure:

```env
VITE_CESIUM_IMAGERY_URL=/cesium-data/imagery
VITE_CESIUM_TERRAIN_URL=/cesium-data/terrain
VITE_CESIUM_3D_TILES_URL=/cesium-data/3d-tiles/tileset.json
```

- `imagery` must be a TMS imagery tileset with `tilemapresource.xml`.
- `terrain` must be Cesium quantized-mesh terrain with `layer.json`.
- `3d-tiles` must contain a valid `tileset.json` and its referenced content.

Only use imagery and terrain datasets whose licenses permit offline storage and use.
