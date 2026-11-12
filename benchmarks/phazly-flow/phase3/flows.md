# Flussi che attraversano il perimetro

Ricavati da `flows.py` (regole di collegamento di phazly, collegamenti con il motore). Per ogni dato letto nel perimetro: chi lo scrive e chi lo legge, con il punto del codice. Granularità e significato non sono etichettati.

## `app state/mealTypes`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createProfileSlice.addMealType` (react-app/src/stores/slices/profileSlice.ts:288); `createProfileSlice.removeMealType` (react-app/src/stores/slices/profileSlice.ts:296); `createProfileSlice.reorderMealTypes` (react-app/src/stores/slices/profileSlice.ts:311); `createProfileSlice.setMealTypes` (react-app/src/stores/slices/profileSlice.ts:274); `createProfileSlice.setWorkoutSlotsEnabled` (react-app/src/stores/slices/profileSlice.ts:322)
- leggono: `QuickAddSheet` (react-app/src/components/common/QuickAddSheet.tsx:77); `useDayLogSlots` (react-app/src/hooks/useDayLogSlots.ts:188); `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:52)

## `app state/activePlanId`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `resetAllData` (react-app/src/stores/appStore.ts:238); `createMealPlanSlice.clearCurrentPlan` (react-app/src/stores/slices/mealPlanSlice.ts:206); `createMealPlanSlice.setActivePlanId` (react-app/src/stores/slices/mealPlanSlice.ts:182)
- leggono: `useDayProgress` (react-app/src/hooks/useDayProgress.ts:37); `useDayTargets` (react-app/src/hooks/useHistoricalDayPlan.ts:259); `useStencilForDate` (react-app/src/hooks/useHistoricalDayPlan.ts:136); `useStencilWeek` (react-app/src/hooks/useHistoricalDayPlan.ts:194); `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:52); `useTabRefresh` (react-app/src/hooks/useTabRefresh.ts:51)

## `app state/completedMeals`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `resetAllData` (react-app/src/stores/appStore.ts:238); `createFavoritesSlice.moveFromStackToMeal` (react-app/src/stores/slices/favoritesSlice.ts:121); `createMealPlanSlice.addMealAddition` (react-app/src/stores/slices/mealPlanSlice.ts:271); `createMealPlanSlice.clearDiaryHistory` (react-app/src/stores/slices/mealPlanSlice.ts:448); `createMealPlanSlice.completeMeal` (react-app/src/stores/slices/mealPlanSlice.ts:215); `createMealPlanSlice.mergeDiaryDays` (react-app/src/stores/slices/mealPlanSlice.ts:505); `createMealPlanSlice.moveMealAddition` (react-app/src/stores/slices/mealPlanSlice.ts:364); `createMealPlanSlice.removeMealAddition` (react-app/src/stores/slices/mealPlanSlice.ts:323); `createMealPlanSlice.resetDay` (react-app/src/stores/slices/mealPlanSlice.ts:428); `createMealPlanSlice.setCompletedMeals` (react-app/src/stores/slices/mealPlanSlice.ts:415); `createMealPlanSlice.uncompleteMeal` (react-app/src/stores/slices/mealPlanSlice.ts:241)
- leggono: `QuickAddSheet` (react-app/src/components/common/QuickAddSheet.tsx:252); `TodayLogCard` (react-app/src/components/home/TodayLogCard.tsx:76); `useDayLogSlots` (react-app/src/hooks/useDayLogSlots.ts:189); `useDayProgress` (react-app/src/hooks/useDayProgress.ts:66); `useHomeTabController.onClick` (react-app/src/hooks/useHomeTabController.ts:419); `useRecentFoods` (react-app/src/hooks/useRecentFoods.ts:41); `useWeeklyDeviation` (react-app/src/hooks/useWeeklyDeviation.ts:58); `createFavoritesSlice.moveFromStackToMeal` (react-app/src/stores/slices/favoritesSlice.ts:121); `createMealPlanSlice.addMealAddition` (react-app/src/stores/slices/mealPlanSlice.ts:271); `createMealPlanSlice.moveMealAddition` (react-app/src/stores/slices/mealPlanSlice.ts:364)

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
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createProfileSlice.endPhase` (react-app/src/stores/slices/profileSlice.ts:421); `createProfileSlice.extendPhase` (react-app/src/stores/slices/profileSlice.ts:440); `createProfileSlice.setUserProfile` (react-app/src/stores/slices/profileSlice.ts:122); `createProfileSlice.startPhase` (react-app/src/stores/slices/profileSlice.ts:391)
- leggono: `useSupplementStatus` (react-app/src/hooks/useSupplementStatus.ts:49); `useWorkoutTracking` (react-app/src/hooks/useWorkoutTracking.ts:25); `createMealPlanSlice.logWorkoutMove` (react-app/src/stores/slices/mealPlanSlice.ts:593)

## `app state/userSupplements`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createSupplementSlice.addSupplement` (react-app/src/stores/slices/supplementSlice.ts:76); `createSupplementSlice.removeSupplement` (react-app/src/stores/slices/supplementSlice.ts:97); `createSupplementSlice.setUserSupplements` (react-app/src/stores/slices/supplementSlice.ts:128); `createSupplementSlice.updateSupplement` (react-app/src/stores/slices/supplementSlice.ts:90)
- leggono: `useSupplementStatus` (react-app/src/hooks/useSupplementStatus.ts:49)

## `app state/currentDay`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createUISlice.syncToday` (react-app/src/stores/slices/uiSlice.ts:119)
- leggono: `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:52); `useToday` (react-app/src/hooks/useToday.ts:30); `useWeeklyDeviation` (react-app/src/hooks/useWeeklyDeviation.ts:44)

## `app state/workoutLog`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `resetAllData` (react-app/src/stores/appStore.ts:238); `createMealPlanSlice.batchLogWorkouts` (react-app/src/stores/slices/mealPlanSlice.ts:601); `createMealPlanSlice.cancelExtraWorkout` (react-app/src/stores/slices/mealPlanSlice.ts:587); `createMealPlanSlice.logWorkout` (react-app/src/stores/slices/mealPlanSlice.ts:577); `createMealPlanSlice.logWorkoutMove` (react-app/src/stores/slices/mealPlanSlice.ts:597); `createMealPlanSlice.planExtraWorkout` (react-app/src/stores/slices/mealPlanSlice.ts:582); `createMealPlanSlice.setWorkoutLog` (react-app/src/stores/slices/mealPlanSlice.ts:608)
- leggono: `useWorkoutTracking` (react-app/src/hooks/useWorkoutTracking.ts:19); `createMealPlanSlice.logWorkoutMove` (react-app/src/stores/slices/mealPlanSlice.ts:597)

## `app state/_planEpoch`
- scrivono: `createMealPlanSlice.bumpPlanEpoch` (react-app/src/stores/slices/mealPlanSlice.ts:563); `createMealPlanSlice.clearCurrentPlan` (react-app/src/stores/slices/mealPlanSlice.ts:206)
- leggono: `useDayTargets` (react-app/src/hooks/useHistoricalDayPlan.ts:260); `useStencilForDate` (react-app/src/hooks/useHistoricalDayPlan.ts:137); `useStencilWeek` (react-app/src/hooks/useHistoricalDayPlan.ts:195)

## `app state/foodStack`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createFavoritesSlice.addToFoodStack` (react-app/src/stores/slices/favoritesSlice.ts:93); `createFavoritesSlice.clearFoodStack` (react-app/src/stores/slices/favoritesSlice.ts:176); `createFavoritesSlice.moveFromStackToMeal` (react-app/src/stores/slices/favoritesSlice.ts:121); `createFavoritesSlice.removeFromFoodStack` (react-app/src/stores/slices/favoritesSlice.ts:104); `createFavoritesSlice.setFoodStack` (react-app/src/stores/slices/favoritesSlice.ts:181)
- leggono: `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:52); `createFavoritesSlice.moveFromStackToMeal` (react-app/src/stores/slices/favoritesSlice.ts:121)

## `app state/homeEditMode`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `resetAllData` (react-app/src/stores/appStore.ts:238); `createHomeLayoutSlice.enterHomeEditMode` (react-app/src/stores/slices/homeLayoutSlice.ts:61); `createHomeLayoutSlice.exitHomeEditMode` (react-app/src/stores/slices/homeLayoutSlice.ts:62)
- leggono: `EditModeToolbar` (react-app/src/components/home/EditModeToolbar.tsx:21); `HomeCardFrame` (react-app/src/components/home/HomeCardFrame.tsx:58); `SortableHomeCards` (react-app/src/components/home/SortableHomeCards.tsx:22); `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:81)

## `app state/userLocation`
- scrivono: `logout` (react-app/src/stores/appStore.ts:272); `createProfileSlice.setUserLocation` (react-app/src/stores/slices/profileSlice.ts:358)
- leggono: `useHomeTabController` (react-app/src/hooks/useHomeTabController.ts:52)


(Elenco troncato al tetto di 12.000 caratteri.)
