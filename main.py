# 1. إكمال دالة حفظ الاسم الجديد
@dp.message(SystemStates.edit_button_new_name)
async def save_new_name(message: types.Message, state: FSMContext):
    new_name = message.text
    data = await state.get_data()
    button_id = data['button_id']
    
    cursor.execute("UPDATE elements SET name=? WHERE id=?", (new_name, button_id))
    conn.commit()
    
    await message.answer(f"✅ تم تغيير اسم الزر إلى: {new_name}")
    await state.clear()

# 2. دالة حذف زر (جديدة)
@dp.callback_query(F.data == "adm_delete_button")
async def ask_delete_id(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("🗑 أرسل ID الزر الذي تريد حذفه نهائياً:")
    await state.set_state(SystemStates.delete_button)

@dp.message(SystemStates.delete_button)
async def process_delete(message: types.Message, state: FSMContext):
    button_id = message.text
    cursor.execute("DELETE FROM elements WHERE id=?", (button_id,))
    
    if cursor.rowcount > 0:
        conn.commit()
        await message.answer("✅ تم حذف الزر بنجاح.")
    else:
        await message.answer("❌ لا يوجد زر بهذا الـ ID.")
    
    await state.clear()

# 3. تعديل رابط الدعم (كمثال، ونفس المنطق للرابط الآخر)
@dp.callback_query(F.data == "change_support")
async def ask_new_support(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("👨‍💻 أرسل الرابط الجديد للدعم الفني:")
    await state.set_state(SystemStates.edit_support_link)

@dp.message(SystemStates.edit_support_link)
async def update_support(message: types.Message, state: FSMContext):
    global MY_ACCOUNT_URL
    MY_ACCOUNT_URL = message.text
    await message.answer(f"✅ تم تحديث رابط الدعم إلى:\n{MY_ACCOUNT_URL}")
    await state.clear()
    
