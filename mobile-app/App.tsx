/**
 * SmartCrop Pakistan - React Native App Entry Point
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

// Screens
import SplashScreen from './src/screens/SplashScreen';
import LoginScreen from './src/screens/LoginScreen';
import HomeScreen from './src/screens/HomeScreen';
import FarmsScreen from './src/screens/FarmsScreen';
import FarmDetailScreen from './src/screens/FarmDetailScreen';
import AddFarmScreen from './src/screens/AddFarmScreen';
import AIAgentScreen from './src/screens/AIAgentScreen';
import AlertsScreen from './src/screens/AlertsScreen';
import ProfileScreen from './src/screens/ProfileScreen';

// Localization
import './src/i18n';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Tab Navigator for main app
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Home') {
            iconName = 'home';
          } else if (route.name === 'Farms') {
            iconName = 'sprout';
          } else if (route.name === 'AI Agent') {
            iconName = 'robot';
          } else if (route.name === 'Alerts') {
            iconName = 'bell';
          } else if (route.name === 'Profile') {
            iconName = 'account';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#2E7D32',
        tabBarInactiveTintColor: 'gray',
        headerShown: false,
      })}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen}
        options={{ tabBarLabel: 'ہوم' }}
      />
      <Tab.Screen 
        name="Farms" 
        component={FarmsScreen}
        options={{ tabBarLabel: 'کھیت' }}
      />
      <Tab.Screen 
        name="AI Agent" 
        component={AIAgentScreen}
        options={{ tabBarLabel: 'AI مدد' }}
      />
      <Tab.Screen 
        name="Alerts" 
        component={AlertsScreen}
        options={{ tabBarLabel: 'الرٹس' }}
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
        options={{ tabBarLabel: 'پروفائل' }}
      />
    </Tab.Navigator>
  );
}

function App(): JSX.Element {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Splash"
          screenOptions={{ headerShown: false }}
        >
          <Stack.Screen name="Splash" component={SplashScreen} />
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Main" component={MainTabs} />
          <Stack.Screen 
            name="FarmDetail" 
            component={FarmDetailScreen}
            options={{ headerShown: true, title: 'کھیت کی تفصیلات' }}
          />
          <Stack.Screen 
            name="AddFarm" 
            component={AddFarmScreen}
            options={{ headerShown: true, title: 'نیا کھیت شامل کریں' }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

export default App;
