/**
 * SmartCrop Pakistan - Home Screen
 * Main dashboard showing farm health overview
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { LineChart } from 'react-native-chart-kit';
import { useNavigation } from '@react-navigation/native';
import { useTranslation } from 'react-i18next';

import { useFarmStore } from '../store/farmStore';
import { colors, spacing, typography } from '../theme';
import HealthScoreCard from '../components/HealthScoreCard';
import WeatherWidget from '../components/WeatherWidget';
import QuickActionButton from '../components/QuickActionButton';

const { width: screenWidth } = Dimensions.get('window');

const HomeScreen: React.FC = () => {
  const { t } = useTranslation();
  const navigation = useNavigation();
  const { farms, fetchFarms, isLoading } = useFarmStore();
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchFarms();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchFarms();
    setRefreshing(false);
  };

  // Calculate overall health from all farms
  const overallHealth = farms.length > 0
    ? farms.reduce((sum, farm) => sum + (farm.healthScore || 0), 0) / farms.length
    : 0;

  // Mock NDVI data for chart
  const ndviData = {
    labels: ['1 ہفتہ', '2 ہفتہ', '3 ہفتہ', '4 ہفتہ', '5 ہفتہ', '6 ہفتہ'],
    datasets: [
      {
        data: [0.52, 0.55, 0.58, 0.61, 0.63, 0.65],
        color: (opacity = 1) => `rgba(46, 125, 50, ${opacity})`,
        strokeWidth: 2,
      },
    ],
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>السلام علیکم! 👋</Text>
            <Text style={styles.subGreeting}>{t('home.welcomeBack')}</Text>
          </View>
          <TouchableOpacity onPress={() => navigation.navigate('Alerts')}>
            <Icon name="bell-outline" size={28} color={colors.primary} />
            {/* Notification badge */}
            <View style={styles.notificationBadge}>
              <Text style={styles.badgeText}>3</Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* Weather Widget */}
        <WeatherWidget />

        {/* Overall Health Card */}
        <View style={styles.healthSection}>
          <Text style={styles.sectionTitle}>📊 {t('home.overallHealth')}</Text>
          <HealthScoreCard 
            score={overallHealth} 
            label={t('home.allFarmsHealth')}
          />
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <Text style={styles.sectionTitle}>⚡ {t('home.quickActions')}</Text>
          <View style={styles.actionGrid}>
            <QuickActionButton
              icon="satellite-variant"
              label={t('home.checkHealth')}
              onPress={() => navigation.navigate('Farms')}
              color="#4CAF50"
            />
            <QuickActionButton
              icon="microphone"
              label={t('home.askAI')}
              onPress={() => navigation.navigate('AI Agent')}
              color="#2196F3"
            />
            <QuickActionButton
              icon="camera"
              label={t('home.scanDisease')}
              onPress={() => {/* Open camera */}}
              color="#FF9800"
            />
            <QuickActionButton
              icon="chart-line"
              label={t('home.yieldPrediction')}
              onPress={() => navigation.navigate('FarmDetail', { farmId: farms[0]?.id })}
              color="#9C27B0"
            />
          </View>
        </View>

        {/* NDVI Trend Chart */}
        <View style={styles.chartSection}>
          <Text style={styles.sectionTitle}>📈 {t('home.ndviTrend')}</Text>
          <Text style={styles.chartSubtitle}>آخری 6 ہفتوں کا رجحان</Text>
          <LineChart
            data={ndviData}
            width={screenWidth - 40}
            height={200}
            chartConfig={{
              backgroundColor: '#ffffff',
              backgroundGradientFrom: '#ffffff',
              backgroundGradientTo: '#ffffff',
              decimalPlaces: 2,
              color: (opacity = 1) => `rgba(46, 125, 50, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              style: { borderRadius: 16 },
              propsForDots: {
                r: '6',
                strokeWidth: '2',
                stroke: '#2E7D32',
              },
            }}
            bezier
            style={styles.chart}
          />
        </View>

        {/* Farms Summary */}
        <View style={styles.farmsSummary}>
          <View style={styles.summaryHeader}>
            <Text style={styles.sectionTitle}>🌾 {t('home.myFarms')}</Text>
            <TouchableOpacity onPress={() => navigation.navigate('Farms')}>
              <Text style={styles.seeAll}>{t('home.seeAll')}</Text>
            </TouchableOpacity>
          </View>
          
          {farms.slice(0, 3).map((farm) => (
            <TouchableOpacity
              key={farm.id}
              style={styles.farmCard}
              onPress={() => navigation.navigate('FarmDetail', { farmId: farm.id })}
            >
              <View style={styles.farmInfo}>
                <Icon name="sprout" size={24} color={colors.primary} />
                <View style={styles.farmText}>
                  <Text style={styles.farmName}>{farm.name}</Text>
                  <Text style={styles.farmDetails}>
                    {farm.areaAcres} ایکڑ • {farm.currentCrop || 'فصل نہیں'}
                  </Text>
                </View>
              </View>
              <View style={styles.farmHealth}>
                <Text style={[
                  styles.healthText,
                  { color: farm.healthScore >= 70 ? colors.success : farm.healthScore >= 50 ? colors.warning : colors.error }
                ]}>
                  {farm.healthScore?.toFixed(0) || '--'}%
                </Text>
                <Icon name="chevron-right" size={24} color={colors.textSecondary} />
              </View>
            </TouchableOpacity>
          ))}

          {farms.length === 0 && (
            <TouchableOpacity
              style={styles.addFarmCard}
              onPress={() => navigation.navigate('AddFarm')}
            >
              <Icon name="plus-circle" size={48} color={colors.primary} />
              <Text style={styles.addFarmText}>{t('home.addFirstFarm')}</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Tips Section */}
        <View style={styles.tipsSection}>
          <Text style={styles.sectionTitle}>💡 {t('home.todayTip')}</Text>
          <View style={styles.tipCard}>
            <Icon name="lightbulb-outline" size={24} color="#FFC107" />
            <Text style={styles.tipText}>
              گندم کی فصل میں پانی کی کمی سے بچنے کے لیے صبح سویرے آبپاشی کریں۔ 
              اس سے پانی کا ضیاع کم ہوگا۔
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    backgroundColor: colors.white,
  },
  greeting: {
    fontSize: typography.sizes.xl,
    fontWeight: 'bold',
    color: colors.textPrimary,
  },
  subGreeting: {
    fontSize: typography.sizes.md,
    color: colors.textSecondary,
    marginTop: 4,
  },
  notificationBadge: {
    position: 'absolute',
    top: -5,
    right: -5,
    backgroundColor: colors.error,
    borderRadius: 10,
    width: 18,
    height: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  badgeText: {
    color: colors.white,
    fontSize: 10,
    fontWeight: 'bold',
  },
  sectionTitle: {
    fontSize: typography.sizes.lg,
    fontWeight: 'bold',
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  healthSection: {
    padding: spacing.lg,
  },
  quickActions: {
    padding: spacing.lg,
    backgroundColor: colors.white,
  },
  actionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  chartSection: {
    padding: spacing.lg,
    backgroundColor: colors.white,
    marginTop: spacing.sm,
  },
  chartSubtitle: {
    fontSize: typography.sizes.sm,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  chart: {
    borderRadius: 16,
  },
  farmsSummary: {
    padding: spacing.lg,
  },
  summaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  seeAll: {
    color: colors.primary,
    fontSize: typography.sizes.md,
  },
  farmCard: {
    backgroundColor: colors.white,
    borderRadius: 12,
    padding: spacing.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  farmInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  farmText: {
    marginLeft: spacing.md,
  },
  farmName: {
    fontSize: typography.sizes.md,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  farmDetails: {
    fontSize: typography.sizes.sm,
    color: colors.textSecondary,
    marginTop: 2,
  },
  farmHealth: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  healthText: {
    fontSize: typography.sizes.lg,
    fontWeight: 'bold',
    marginRight: spacing.sm,
  },
  addFarmCard: {
    backgroundColor: colors.white,
    borderRadius: 12,
    padding: spacing.xl,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: colors.primary,
    borderStyle: 'dashed',
  },
  addFarmText: {
    fontSize: typography.sizes.md,
    color: colors.primary,
    marginTop: spacing.sm,
  },
  tipsSection: {
    padding: spacing.lg,
    marginBottom: spacing.xl,
  },
  tipCard: {
    backgroundColor: '#FFF9E6',
    borderRadius: 12,
    padding: spacing.md,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  tipText: {
    flex: 1,
    marginLeft: spacing.sm,
    fontSize: typography.sizes.md,
    color: colors.textPrimary,
    lineHeight: 24,
  },
});

export default HomeScreen;
