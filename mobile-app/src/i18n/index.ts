/**
 * SmartCrop Pakistan - i18n Configuration
 * Multi-language support: Urdu, Punjabi, Sindhi, English
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  ur: {
    translation: {
      // Common
      common: {
        loading: 'لوڈ ہو رہا ہے...',
        error: 'خرابی',
        success: 'کامیاب',
        cancel: 'منسوخ',
        save: 'محفوظ کریں',
        delete: 'حذف کریں',
        edit: 'ترمیم',
        confirm: 'تصدیق کریں',
        back: 'واپس',
        next: 'اگلا',
        done: 'ہو گیا',
        retry: 'دوبارہ کوشش کریں',
      },
      
      // Home Screen
      home: {
        welcomeBack: 'SmartCrop میں خوش آمدید',
        overallHealth: 'مجموعی صحت',
        allFarmsHealth: 'تمام کھیتوں کی صحت',
        quickActions: 'فوری کارروائیاں',
        checkHealth: 'صحت چیک کریں',
        askAI: 'AI سے پوچھیں',
        scanDisease: 'بیماری اسکین',
        yieldPrediction: 'پیداوار کی پیشنگوئی',
        ndviTrend: 'NDVI رجحان',
        myFarms: 'میرے کھیت',
        seeAll: 'سب دیکھیں',
        addFirstFarm: 'اپنا پہلا کھیت شامل کریں',
        todayTip: 'آج کی ٹپ',
      },
      
      // Farms
      farms: {
        title: 'میرے کھیت',
        addFarm: 'کھیت شامل کریں',
        farmName: 'کھیت کا نام',
        area: 'رقبہ',
        acres: 'ایکڑ',
        crop: 'فصل',
        irrigationType: 'آبپاشی کی قسم',
        canal: 'نہر',
        tubewell: 'ٹیوب ویل',
        rainfed: 'بارانی',
        plantingDate: 'بوائی کی تاریخ',
        healthScore: 'صحت سکور',
        lastUpdated: 'آخری اپڈیٹ',
        noFarms: 'کوئی کھیت نہیں ملا',
        drawBoundary: 'کھیت کی حدود بنائیں',
      },
      
      // Crops
      crops: {
        wheat: 'گندم',
        rice: 'چاول',
        cotton: 'کپاس',
        sugarcane: 'گنا',
        maize: 'مکئی',
      },
      
      // Health
      health: {
        healthy: 'صحت مند',
        moderate: 'معتدل',
        stressed: 'دباؤ میں',
        critical: 'نازک',
        waterStressed: 'پانی کی کمی',
        nutrientDeficient: 'غذائیت کی کمی',
        pestInfected: 'کیڑوں کا حملہ',
        diseaseAffected: 'بیماری سے متاثر',
        analyzing: 'تجزیہ ہو رہا ہے...',
        lastAnalysis: 'آخری تجزیہ',
      },
      
      // AI Agent
      agent: {
        title: 'AI زرعی مشیر',
        placeholder: 'یہاں لکھیں یا آواز سے بولیں...',
        recording: 'آواز ریکارڈ ہو رہی ہے...',
        thinking: 'سوچ رہا ہوں...',
        suggestions: 'تجویز کردہ سوالات',
      },
      
      // Alerts
      alerts: {
        title: 'الرٹس',
        pest: 'کیڑوں کا الرٹ',
        disease: 'بیماری کا الرٹ',
        water: 'پانی کا الرٹ',
        weather: 'موسم کا الرٹ',
        noAlerts: 'کوئی الرٹ نہیں',
        markRead: 'پڑھا گیا',
        viewAll: 'سب دیکھیں',
      },
      
      // Profile
      profile: {
        title: 'میرا پروفائل',
        name: 'نام',
        phone: 'فون نمبر',
        district: 'ضلع',
        province: 'صوبہ',
        language: 'زبان',
        notifications: 'اطلاعات',
        logout: 'لاگ آؤٹ',
        support: 'مدد',
        about: 'SmartCrop کے بارے میں',
      },
      
      // Weather
      weather: {
        temperature: 'درجہ حرارت',
        humidity: 'نمی',
        rainfall: 'بارش',
        forecast: 'موسم کی پیشنگوئی',
      },
      
      // Yield
      yield: {
        prediction: 'پیداوار کی پیشنگوئی',
        predicted: 'متوقع پیداوار',
        tonsPerHectare: 'ٹن فی ہیکٹر',
        confidence: 'اعتماد',
        harvestDate: 'فصل کاٹنے کی تاریخ',
        daysRemaining: 'باقی دن',
        revenue: 'متوقع آمدنی',
      },
    },
  },
  
  // Punjabi (simplified - would need proper translation)
  pa: {
    translation: {
      home: {
        welcomeBack: 'SmartCrop وچ جی آیاں نوں',
        // ... more Punjabi translations
      },
    },
  },
  
  // English
  en: {
    translation: {
      common: {
        loading: 'Loading...',
        error: 'Error',
        success: 'Success',
        cancel: 'Cancel',
        save: 'Save',
        delete: 'Delete',
        edit: 'Edit',
        confirm: 'Confirm',
        back: 'Back',
        next: 'Next',
        done: 'Done',
        retry: 'Retry',
      },
      home: {
        welcomeBack: 'Welcome to SmartCrop',
        overallHealth: 'Overall Health',
        allFarmsHealth: 'All Farms Health',
        quickActions: 'Quick Actions',
        checkHealth: 'Check Health',
        askAI: 'Ask AI',
        scanDisease: 'Scan Disease',
        yieldPrediction: 'Yield Prediction',
        ndviTrend: 'NDVI Trend',
        myFarms: 'My Farms',
        seeAll: 'See All',
        addFirstFarm: 'Add Your First Farm',
        todayTip: 'Today\'s Tip',
      },
    },
  },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'ur', // Default language: Urdu
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
