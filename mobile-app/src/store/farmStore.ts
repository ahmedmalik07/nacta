/**
 * SmartCrop Pakistan - Farm Store (Zustand)
 */

import { create } from 'zustand';
import { apiClient } from '../services/api';

export interface Farm {
  id: number;
  name: string;
  areaAcres: number;
  centerLat: number;
  centerLon: number;
  currentCrop: string | null;
  plantingDate: string | null;
  irrigationType: string;
  healthScore: number | null;
  ndviLatest: number | null;
  ndwiLatest: number | null;
  lastSatelliteAnalysis: string | null;
}

interface FarmState {
  farms: Farm[];
  selectedFarm: Farm | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchFarms: () => Promise<void>;
  selectFarm: (farmId: number) => void;
  addFarm: (farmData: Partial<Farm>) => Promise<void>;
  updateFarmHealth: (farmId: number) => Promise<void>;
  deleteFarm: (farmId: number) => Promise<void>;
}

export const useFarmStore = create<FarmState>((set, get) => ({
  farms: [],
  selectedFarm: null,
  isLoading: false,
  error: null,

  fetchFarms: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get('/farms/');
      set({ 
        farms: response.data.farms.map((f: any) => ({
          id: f.id,
          name: f.name,
          areaAcres: f.area_acres,
          centerLat: f.center_lat,
          centerLon: f.center_lon,
          currentCrop: f.current_crop,
          plantingDate: f.planting_date,
          irrigationType: f.irrigation_type,
          healthScore: f.health_score,
          ndviLatest: f.ndvi_latest,
          ndwiLatest: f.ndwi_latest,
          lastSatelliteAnalysis: f.last_satellite_analysis,
        })),
        isLoading: false 
      });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  selectFarm: (farmId: number) => {
    const farm = get().farms.find(f => f.id === farmId);
    set({ selectedFarm: farm || null });
  },

  addFarm: async (farmData: Partial<Farm>) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.post('/farms/', {
        name: farmData.name,
        area_acres: farmData.areaAcres,
        boundary_points: [], // Would come from map drawing
        current_crop: farmData.currentCrop,
        irrigation_type: farmData.irrigationType,
      });
      await get().fetchFarms();
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  updateFarmHealth: async (farmId: number) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post('/health/analyze', {
        farm_id: farmId,
        source: 'sentinel-2',
      });
      
      // Update local state
      set(state => ({
        farms: state.farms.map(f => 
          f.id === farmId 
            ? { 
                ...f, 
                healthScore: response.data.health_score,
                ndviLatest: response.data.ndvi,
                ndwiLatest: response.data.ndwi,
              }
            : f
        ),
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  deleteFarm: async (farmId: number) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.delete(`/farms/${farmId}`);
      set(state => ({
        farms: state.farms.filter(f => f.id !== farmId),
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },
}));
