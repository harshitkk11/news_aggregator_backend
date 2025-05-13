# from internal.src.services.preferenceService import PreferenceService

# class PreferenceController:
#     def __init__(self):
#         self.preference_service = PreferenceService()

#     def get_preferences(self, user_id: str):
#         preferences = self.preference_service.get_preferences(user_id)
#         return preferences

from internal.src.services.preferenceService import PreferenceService

class PreferenceController:
    def __init__(self):
        self.preference_service = PreferenceService()

    async def get_preferences(self, user_id: str):
        preferences = await self.preference_service.get_preferences(user_id)
        return preferences
