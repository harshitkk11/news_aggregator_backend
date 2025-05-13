# from internal.src.repositories.preferenceRepository import PreferenceRepository

# class PreferenceService:
#     def __init__(self):
#         self.preference_repo = PreferenceRepository()

#     def get_preferences(self, user_id: str):
#         count = self.preference_repo.get_user_preference_count(user_id)
#         if count == 0:
#             self.preference_repo.populate_default_preferences(user_id)
        
#         preference_items = self.preference_repo.get_active_preference_items()
#         user_preferences = self.preference_repo.get_existing_preferences(user_id)

#         pref_map = {pref['preference_item_id']: pref['status'] for pref in user_preferences}
#         result = []
#         for item in preference_items:
#             enabled = pref_map.get(item['id'], False)
#             result.append({
#                 "id": item['id'],
#                 "name": item['category'],
#                 "enabled": enabled
#             })

#         return result


from internal.src.repositories.preferenceRepository import PreferenceRepository

class PreferenceService:
    def __init__(self):
        self.preference_repo = PreferenceRepository()

    async def get_preferences(self, user_id: str):
        # Ensure that async calls are awaited
        count = await self.preference_repo.get_user_preference_count(user_id)
        if count == 0:
            await self.preference_repo.populate_default_preferences(user_id)

        preference_items = await self.preference_repo.get_active_preference_items()
        user_preferences = await self.preference_repo.get_existing_preferences(user_id)

        pref_map = {pref['preference_item_id']: pref['status'] for pref in user_preferences}
        result = []
        for item in preference_items:
            enabled = pref_map.get(item['id'], False)
            result.append({
                "id": item['id'],
                "name": item['category'],
                "enabled": enabled
            })

        return result
