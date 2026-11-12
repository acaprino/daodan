# Flussi che attraversano il perimetro

Ricavati da `flows.py` (regole di collegamento di phazly, collegamenti con il motore). Per ogni dato letto nel perimetro: chi lo scrive e chi lo legge, con il punto del codice. Granularità e significato non sono etichettati.

## `app state/mealTypes`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createProfileSlice.addMealType` (react-app/src/stores/slices/profileSlice.ts:288); `createProfileSlice.removeMealType` (react-app/src/stores/slices/profileSlice.ts:296); `createProfileSlice.reorderMealTypes` (react-app/src/stores/slices/profileSlice.ts:311); `createProfileSlice.setMealTypes` (react-app/src/stores/slices/profileSlice.ts:274); `createProfileSlice.setWorkoutSlotsEnabled` (react-app/src/stores/slices/profileSlice.ts:322)
- leggono: `QuickAddSheet` (react-app/src/components/common/QuickAddSheet.tsx:77); `useDayLogSlots` (react-app/src/hooks/useDayLogSlots.ts:188); `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:52); `createFavoritesSlice.getFavoritesByMealSlot` (react-app/src/stores/slices/favoritesSlice.ts:73); `createFavoritesSlice.isFavorite` (react-app/src/stores/slices/favoritesSlice.ts:80)

## `app state/completedMeals`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `resetAllData` (react-app/src/stores/appStore.ts:238); `createMealPlanSlice.clearDiaryHistory` (react-app/src/stores/slices/mealPlanSlice.ts:448); `createMealPlanSlice.completeMeal` (react-app/src/stores/slices/mealPlanSlice.ts:215); `createMealPlanSlice.removeMealAddition` (react-app/src/stores/slices/mealPlanSlice.ts:323); `createMealPlanSlice.resetDay` (react-app/src/stores/slices/mealPlanSlice.ts:428); `createMealPlanSlice.setCompletedMeals` (react-app/src/stores/slices/mealPlanSlice.ts:415); `createMealPlanSlice.uncompleteMeal` (react-app/src/stores/slices/mealPlanSlice.ts:241)
- leggono: `QuickAddSheet` (react-app/src/components/common/QuickAddSheet.tsx:252); `TodayLogCard` (react-app/src/components/home/TodayLogCard.tsx:76); `useDayLogSlots` (react-app/src/hooks/useDayLogSlots.ts:189); `useDayProgress` (react-app/src/hooks/useDayProgress.ts:66); `useHomeTabController.onClick` (react-app/src/hooks/useHomeTabController.ts:419); `useRecentFoods` (react-app/src/hooks/useRecentFoods.ts:41); `useWeeklyDeviation` (react-app/src/hooks/useWeeklyDeviation.ts:58); `createFavoritesSlice.getFavoritesByMealSlot` (react-app/src/stores/slices/favoritesSlice.ts:73); `createFavoritesSlice.isFavorite` (react-app/src/stores/slices/favoritesSlice.ts:80); `createFavoritesSlice.moveFromStackToMeal` (react-app/src/stores/slices/favoritesSlice.ts:112); `createMealPlanSlice.addMealAddition` (react-app/src/stores/slices/mealPlanSlice.ts:261); `createMealPlanSlice.moveMealAddition` (react-app/src/stores/slices/mealPlanSlice.ts:356)

## `app state/activePlanId`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `resetAllData` (react-app/src/stores/appStore.ts:238); `createMealPlanSlice.clearCurrentPlan` (react-app/src/stores/slices/mealPlanSlice.ts:206); `createMealPlanSlice.setActivePlanId` (react-app/src/stores/slices/mealPlanSlice.ts:182)
- leggono: `useDayProgress` (react-app/src/hooks/useDayProgress.ts:37); `useDayTargets` (react-app/src/hooks/useHistoricalDayPlan.ts:259); `useStencilForDate` (react-app/src/hooks/useHistoricalDayPlan.ts:136); `useStencilWeek` (react-app/src/hooks/useHistoricalDayPlan.ts:194); `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:52); `useTabRefresh` (react-app/src/hooks/useTabRefresh.ts:51)

## `app state/currentPlan`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `resetAllData` (react-app/src/stores/appStore.ts:238); `createMealPlanSlice.clearCurrentPlan` (react-app/src/stores/slices/mealPlanSlice.ts:206); `createMealPlanSlice.clearMealPlanCache` (react-app/src/stores/slices/mealPlanSlice.ts:194); `createMealPlanSlice.setCurrentPlan` (react-app/src/stores/slices/mealPlanSlice.ts:189)
- leggono: `useStencilForDate` (react-app/src/hooks/useHistoricalDayPlan.ts:138); `useStencilWeek` (react-app/src/hooks/useHistoricalDayPlan.ts:196); `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:52); `useHasPlan` (react-app/src/hooks/useMealPlan.ts:68); `useMealPlan` (react-app/src/hooks/useMealPlan.ts:17)

## `app state/userId`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createProfileSlice.setUserId` (react-app/src/stores/slices/profileSlice.ts:387)
- leggono: `fetchRange` (react-app/src/hooks/useDiaryWindow.ts:72); `useDiaryWindow` (react-app/src/hooks/useDiaryWindow.ts:104); `useDayTargets` (react-app/src/hooks/useHistoricalDayPlan.ts:258); `useStencilForDate` (react-app/src/hooks/useHistoricalDayPlan.ts:135); `useStencilWeek` (react-app/src/hooks/useHistoricalDayPlan.ts:193)

## `app state/locale`
- scrivono: `createUISlice.setLocale` (react-app/src/stores/slices/uiSlice.ts:167)
- leggono: `CalmMealBody` (react-app/src/components/home/calm/CalmDayMeals.tsx:174); `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:52)

## `app state/macroTargets`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `resetAllData` (react-app/src/stores/appStore.ts:238); `createProfileSlice.acceptMacroTargets` (react-app/src/stores/slices/profileSlice.ts:230); `createProfileSlice.recalculateMacros` (react-app/src/stores/slices/profileSlice.ts:152); `createProfileSlice.resetMacroTargets` (react-app/src/stores/slices/profileSlice.ts:267); `createProfileSlice.setMacroTargets` (react-app/src/stores/slices/profileSlice.ts:220); `createProfileSlice.updateMacroTarget` (react-app/src/stores/slices/profileSlice.ts:236)
- leggono: `useDayProgress` (react-app/src/hooks/useDayProgress.ts:30); `useWeeklyDeviation` (react-app/src/hooks/useWeeklyDeviation.ts:44)

## `app state/userProfile`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createProfileSlice.endPhase` (react-app/src/stores/slices/profileSlice.ts:421); `createProfileSlice.extendPhase` (react-app/src/stores/slices/profileSlice.ts:440); `createProfileSlice.setUserProfile` (react-app/src/stores/slices/profileSlice.ts:122)
- leggono: `useSupplementStatus` (react-app/src/hooks/useSupplementStatus.ts:49); `useWorkoutTracking` (react-app/src/hooks/useWorkoutTracking.ts:25); `createMealPlanSlice.logWorkoutMove` (react-app/src/stores/slices/mealPlanSlice.ts:593)

## `app state/userSupplements`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createSupplementSlice.addSupplement` (react-app/src/stores/slices/supplementSlice.ts:76); `createSupplementSlice.removeSupplement` (react-app/src/stores/slices/supplementSlice.ts:97); `createSupplementSlice.setUserSupplements` (react-app/src/stores/slices/supplementSlice.ts:128); `createSupplementSlice.updateSupplement` (react-app/src/stores/slices/supplementSlice.ts:90)
- leggono: `useSupplementStatus` (react-app/src/hooks/useSupplementStatus.ts:49)

## `app state/currentDay`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createUISlice.syncToday` (react-app/src/stores/slices/uiSlice.ts:119)
- leggono: `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:52); `useToday` (react-app/src/hooks/useToday.ts:30); `useWeeklyDeviation` (react-app/src/hooks/useWeeklyDeviation.ts:44)

## `app state/foodStack`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createFavoritesSlice.addToFoodStack` (react-app/src/stores/slices/favoritesSlice.ts:93); `createFavoritesSlice.clearFoodStack` (react-app/src/stores/slices/favoritesSlice.ts:176); `createFavoritesSlice.removeFromFoodStack` (react-app/src/stores/slices/favoritesSlice.ts:104); `createFavoritesSlice.setFoodStack` (react-app/src/stores/slices/favoritesSlice.ts:181)
- leggono: `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:52); `createFavoritesSlice.getFavoritesByMealSlot` (react-app/src/stores/slices/favoritesSlice.ts:73); `createFavoritesSlice.isFavorite` (react-app/src/stores/slices/favoritesSlice.ts:80); `createFavoritesSlice.moveFromStackToMeal` (react-app/src/stores/slices/favoritesSlice.ts:112)


(Elenco troncato al tetto di 12.000 caratteri.)
