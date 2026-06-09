# c_my_inventory.py
import streamlit as st
from datetime import date, timedelta
import time
from c_helpers import save_company_image  # Exact image saver function from your project


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _days_until_expiry(expiry_str):
    """Return days until expiry, or None if no date set."""
    if not expiry_str:
        return None
    try:
        return (date.fromisoformat(str(expiry_str)) - date.today()).days
    except (ValueError, TypeError):
        return None


def _expiry_status(days):
    """Return (css_class, label, emoji) for a given days-until-expiry value."""
    if days is None:
        return "inv-badge-ok", "No Expiry", "✅"
    if days < 0:
        return "inv-badge-expired", "EXPIRED", "❌"
    if days <= 7:
        return "inv-badge-urgent", f"{days}d left", "🚨"
    if days <= 14:
        return "inv-badge-warn", f"{days}d left", "⚠️"
    return "inv-badge-ok", f"{days}d left", "✅"


def _extract_image_and_notes(notes_field):
    """Extracts hidden image URL from the notes field if it exists."""
    if not notes_field:
        return None, ""
    if "||IMG:" in notes_field:
        parts = notes_field.split("||IMG:")
        clean_notes = parts[0].strip()
        img_url = parts[1].strip()
        return img_url, clean_notes
    return None, notes_field


UNITS = ["kg", "g", "L", "mL", "pcs", "boxes", "cartons", "bags", "bottles", "rolls"]
CATEGORIES = [
    "Groceries & Food", "Household", "Electronics",
    "Fashion & Apparel", "Lifestyle & Hobbies", "Others",
]


# ── CSS ───────────────────────────────────────────────────────────────────────

INVENTORY_CSS = """
<style>
/* ── Page header ── */
.inv-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #0d6efd 100%);
    border-radius: 14px;
    padding: 32px 36px;
    margin-bottom: 28px;
    box-shadow: 0 10px 30px rgba(0,0,0,.10);
}
.inv-header h1 { color: #fff !important; margin: 0 0 6px 0; }
.inv-header p  { color: rgba(255,255,255,.75) !important; margin: 0; font-size: .95rem; }

/* ── Summary metric cards ── */
.inv-metric-row  { display: flex; gap: 14px; margin-bottom: 24px; flex-wrap: wrap; }
.inv-metric-card {
    flex: 1; min-width: 160px;
    background: white;
    border: 1px solid #bfdbfe;
    border-top: 3px solid #0d6efd;
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.inv-metric-val   { font-size: 1.8rem; font-weight: 700; color: #1e3a5f; line-height: 1; }
.inv-metric-label { font-size: .75rem; color: #64748b; text-transform: uppercase;
                    font-weight: 600; margin-top: 4px; }

/* ── Item Card Layout matching c_my_items Style ── */
.my-item-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 4px;
}
.my-item-title {
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: #1e293b !important;
    margin-bottom: 8px !important;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.my-item-row {
    font-size: 0.9rem !important;
    color: #475569 !important;
    margin-bottom: 4px !important;
}

/* ── Badges ── */
.inv-stock-badge {
    display: inline-block; font-weight: 700; font-size: .8rem;
    padding: 3px 10px; border-radius: 999px;
    border: 1px solid currentColor;
}
.inv-badge-ok      { color: #15803d; background: #dcfce7; border-color: #86efac; }
.inv-badge-warn    { color: #92400e; background: #fef3c7; border-color: #fcd34d; }
.inv-badge-urgent  { color: #9a3412; background: #ffedd5; border-color: #fdba74; }
.inv-badge-expired { color: #991b1b; background: #fee2e2; border-color: #fca5a5; }

/* ── Section heading ── */
.inv-section-heading {
    font-size: 1.1rem; font-weight: 700; color: #1e3a5f;
    padding: 10px 0 6px 0;
    border-bottom: 2px solid #bfdbfe;
    margin-bottom: 16px;
}
</style>
"""


# ── MAIN PAGE ─────────────────────────────────────────────────────────────────

def render_company_inventory_page(db, user_id):
    st.markdown(INVENTORY_CSS, unsafe_allow_html=True)

    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown("""
    <div class="inv-header">
        <h1>📦 My Inventory</h1>
        <p>Track stock levels, expiry dates, and usage across your company's inventory</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Load data ─────────────────────────────────────────────────────────────
    items = db.get_inventory_by_company(user_id) or []

    # ── Summary metrics ───────────────────────────────────────────────────────
    total_items   = len(items)
    expiring_soon = sum(
        1 for i in items
        if (d := _days_until_expiry(i.get("expiry_date"))) is not None and 0 <= d <= 14
    )
    expired_count = sum(
        1 for i in items
        if (d := _days_until_expiry(i.get("expiry_date"))) is not None and d < 0
    )

    st.markdown(f"""
    <div class="inv-metric-row">
        <div class="inv-metric-card">
            <div class="inv-metric-val">{total_items}</div>
            <div class="inv-metric-label">Total Items</div>
        </div>
        <div class="inv-metric-card">
            <div class="inv-metric-val" style="color:#f59e0b">{expiring_soon}</div>
            <div class="inv-metric-label">Expiring ≤ 14 Days</div>
        </div>
        <div class="inv-metric-card">
            <div class="inv-metric-val" style="color:#ef4444">{expired_count}</div>
            <div class="inv-metric-label">Expired</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Expiry alert banners ──────────────────────────────────────────────────
    urgent = [
        i for i in items
        if (d := _days_until_expiry(i.get("expiry_date"))) is not None and 0 <= d <= 14
    ]
    if urgent:
        st.markdown(
            '<div class="inv-section-heading">🚨 Expiry Alerts</div>',
            unsafe_allow_html=True,
        )
        for it in urgent:
            days   = _days_until_expiry(it.get("expiry_date"))
            qty    = it.get("quantity", 0)
            unit   = it.get("unit", "")
            banner_color = "#f59e0b" if days > 7 else "#ef4444"
            border_color = "#fbbf24" if days > 7 else "#fca5a5"
            bg_color     = "#fffbeb" if days > 7 else "#fef2f2"
            txt_color    = "#78350f" if days > 7 else "#991b1b"
            label        = f"{days}d left" if days > 0 else "TODAY"
            st.markdown(f"""
            <div style="background:{bg_color};border:1px solid {border_color};
            border-left:4px solid {banner_color};border-radius:10px;
            padding:14px 18px;margin-bottom:8px;">
                <b style="color:{txt_color};">
                    {'⚠️' if days > 7 else '🚨'} {it['item_name']}
                    &nbsp;·&nbsp; {qty} {unit}
                    &nbsp;·&nbsp; Expires {it.get('expiry_date')} ({label})
                </b>
                <p style="margin:4px 0 0 0;font-size:.83rem;color:{txt_color};">
                    Consider using this stock or moving it to the marketplace before it expires.
                </p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("")

    # ── ADD NEW ITEM WITH PREVIEW ─────────────────────────────────────────────
    st.markdown(
        '<div class="inv-section-heading">➕ Add Inventory Item</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Add a new item to inventory", expanded=(total_items == 0)):
        col_main, col_side = st.columns([2, 1])
        
        with col_main:
            new_name     = st.text_input("Item Name *", key="inv_new_name")
            new_category = st.selectbox("Category", CATEGORIES, key="inv_new_cat")
            new_supplier = st.text_input("Supplier / Brand", key="inv_new_supplier", placeholder="Optional")
            
            c_qty, c_unit = st.columns(2)
            with c_qty:
                new_qty  = st.number_input("Quantity *", min_value=0.0, step=1.0, format="%.2f", key="inv_new_qty")
            with c_unit:
                new_unit = st.selectbox("Unit", UNITS, key="inv_new_unit")
                
            new_has_expiry = st.checkbox("This item has an expiry date", key="inv_new_has_exp")
            new_expiry = (
                st.date_input("Expiry Date", key="inv_new_expiry", min_value=date.today())
                if new_has_expiry else None
            )
            new_notes = st.text_area("Notes (optional)", key="inv_new_notes",
                                     placeholder="Storage location, batch number, etc.", height=68)
            
        with col_side:
            st.markdown("#### 🖼️ Item Image")
            uploaded_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png", "webp"], key="inv_new_img")
            
            if uploaded_file:
                st.image(uploaded_file, caption="Image Preview", use_container_width=True)

        if st.button("✅ Add Item", key="inv_btn_add", use_container_width=True):
            if not new_name.strip():
                st.error("Please enter an item name.")
            elif new_qty < 0:
                st.error("Quantity cannot be negative.")
            else:
                image_url = None
                if uploaded_file:
                    with st.spinner("Uploading item image..."):
                        image_url = save_company_image(uploaded_file)

                # Combine raw notes data with image link safely into the existing notes footprint
                final_notes = new_notes.strip()
                if image_url:
                    final_notes = f"{final_notes} ||IMG:{image_url}".strip()

                # Fully preserves existing DB arguments constraint signature!
                result = db.add_inventory_item(
                    company_id   = user_id,
                    item_name    = new_name.strip(),
                    category     = new_category,
                    quantity     = float(new_qty),
                    unit         = new_unit,
                    supplier     = new_supplier.strip() or None,
                    expiry_date  = new_expiry.isoformat() if new_expiry else None,
                    notes        = final_notes if final_notes else None,
                )
                if result.get("success"):
                    st.success(f"✅ '{new_name.strip()}' added to inventory.")
                    time.sleep(0.4)
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('error', 'Could not add item.')}")

    st.markdown("")

    # ── INVENTORY LIST ────────────────────────────────────────────────────────
    if not items:
        st.info("No inventory items yet. Add one above to get started!")
        return

    # ── Search / filter bar ───────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns([3, 2, 2])
    with fc1:
        search_q = st.text_input("Search inventory", placeholder="🔍 Search by name…",
                                 key="inv_search", label_visibility="collapsed")
    with fc2:
        filter_cat = st.selectbox("Filter Category", ["All Categories"] + CATEGORIES,
                                  key="inv_filter_cat", label_visibility="collapsed")
    with fc3:
        filter_exp = st.selectbox("Expiry Filter", ["All Items", "Expiring ≤ 14 Days", "Expired", "No Expiry"],
                                  key="inv_filter_exp", label_visibility="collapsed")

    # Apply filters
    visible = list(items)
    if search_q:
        visible = [i for i in visible if search_q.lower() in i["item_name"].lower()]
    if filter_cat != "All Categories":
        visible = [i for i in visible if i.get("category") == filter_cat]
    if filter_exp == "Expiring ≤ 14 Days":
        visible = [i for i in visible if (d := _days_until_expiry(i.get("expiry_date"))) is not None and 0 <= d <= 14]
    elif filter_exp == "Expired":
        visible = [i for i in visible if (d := _days_until_expiry(i.get("expiry_date"))) is not None and d < 0]
    elif filter_exp == "No Expiry":
        visible = [i for i in visible if not i.get("expiry_date")]

    st.markdown(
        f'<div class="inv-section-heading">📋 Inventory Items &nbsp;<span style="font-size:.85rem;'
        f'font-weight:400;color:#64748b">({len(visible)} shown)</span></div>',
        unsafe_allow_html=True,
    )

    if not visible:
        st.info("No items match your filters.")
        return

    # Sort logic
    def sort_key(i):
        d = _days_until_expiry(i.get("expiry_date"))
        if d is None:
            return (2, 0, i["item_name"])
        if d < 0:
            return (0, d, i["item_name"])
        return (1, d, i["item_name"])

    visible.sort(key=sort_key)

    # ── RENDER ITEMS MATCHING C_MY_ITEMS CARD LAYOUT ──────────────────────────
    for item in visible:
        item_id = item["id"]
        days    = _days_until_expiry(item.get("expiry_date"))
        badge_cls, badge_lbl, badge_emoji = _expiry_status(days)

        cat      = item.get("category") or "—"
        supplier = item.get("supplier") or "—"
        qty      = item.get("quantity", 0)
        unit     = item.get("unit", "")
        exp_str  = item.get("expiry_date") or "No expiry date"
        
        # Safely extract dynamic image link out of the notes field string wrapper
        raw_notes = item.get("notes") or ""
        img_url, display_notes = _extract_image_and_notes(raw_notes)

        # Streamlit Native Card Row (1:2 image to info structural columns)
        img_col, info_col = st.columns([1, 2])
        
        with img_col:
            if img_url:
                st.image(img_url, use_container_width=True)
            else:
                st.markdown(
                    "<div style='height:140px;background:#f0fdf4;border-radius:10px;"
                    "display:flex;align-items:center;justify-content:center;"
                    "color:#86efac;font-size:2.5rem'>🏭</div>",
                    unsafe_allow_html=True,
                )

        with info_col:
            badge_html = f'<span class="inv-stock-badge {badge_cls}">{badge_emoji} {badge_lbl}</span>'
            notes_html = f"<div class='my-item-row' style='color:#94a3b8; font-style:italic;'>📝 <strong>Notes:</strong> {display_notes}</div>" if display_notes.strip() else ""
            
            st.markdown(f"""
            <div class="my-item-card">
                <p class="my-item-title">{item['item_name']} {badge_html}</p>
                <div class="my-item-row">🏷️ <strong>Category:</strong> {cat}</div>
                <div class="my-item-row">📦 <strong>Stock:</strong> {qty} {unit}</div>
                <div class="my-item-row">🏭 <strong>Supplier:</strong> {supplier}</div>
                <div class="my-item-row">📅 <strong>Expiry:</strong> {exp_str}</div>
                {notes_html}
            </div>
            """, unsafe_allow_html=True)

            action_cols = st.columns([2, 2, 1])

            # ── Record Usage ──────────────────────────────────────────────────
            with action_cols[0]:
                usage_key = f"inv_show_use_{item_id}"
                if st.button("📉 Record Usage", key=f"inv_use_btn_{item_id}", use_container_width=True):
                    st.session_state[usage_key] = not st.session_state.get(usage_key, False)

                if st.session_state.get(usage_key, False):
                    used = st.number_input(
                        f"Quantity used ({unit})", min_value=0.0,
                        max_value=float(qty) if qty >= 0 else 0.0, step=1.0,
                        format="%.2f", key=f"inv_used_qty_{item_id}",
                    )
                    use_note = st.text_input("Usage note (optional)", key=f"inv_use_note_{item_id}")
                    
                    if st.button("✅ Confirm Usage", key=f"inv_confirm_use_{item_id}", use_container_width=True):
                        if used <= 0:
                            st.warning("Enter a quantity greater than 0.")
                        else:
                            new_qty = max(0.0, float(qty) - float(used))
                            res = db.update_inventory_quantity(item_id, user_id, new_qty, note=use_note.strip() or None)
                            if res.get("success"):
                                st.success(f"Stock updated to {new_qty} {unit}")
                                st.session_state[usage_key] = False
                                time.sleep(0.4)
                                st.rerun()
                            else:
                                st.error(f"❌ {res.get('error', 'Update failed.')}")

            # ── Edit Item Framework ───────────────────────────────────────────
            with action_cols[1]:
                edit_key = f"inv_show_edit_{item_id}"
                if st.button("✏️ Edit", key=f"inv_edit_btn_{item_id}", use_container_width=True):
                    st.session_state[edit_key] = not st.session_state.get(edit_key, False)

                if st.session_state.get(edit_key, False):
                    st.markdown("---")
                    e_main, e_side = st.columns([2, 1])
                    with e_main:
                        edit_name     = st.text_input("Name", value=item["item_name"], key=f"inv_edit_name_{item_id}")
                        edit_category = st.selectbox(
                            "Category", CATEGORIES,
                            index=CATEGORIES.index(cat) if cat in CATEGORIES else 0,
                            key=f"inv_edit_cat_{item_id}",
                        )
                        edit_supplier = st.text_input("Supplier", value=supplier if supplier != "—" else "", key=f"inv_edit_sup_{item_id}")
                        edit_qty      = st.number_input("Quantity", min_value=0.0, step=1.0, format="%.2f", value=float(qty), key=f"inv_edit_qty_{item_id}")
                        edit_unit     = st.selectbox("Unit", UNITS, index=UNITS.index(unit) if unit in UNITS else 0, key=f"inv_edit_unit_{item_id}")
                        
                        current_expiry = item.get("expiry_date")
                        has_exp = st.checkbox("Has expiry date", value=bool(current_expiry), key=f"inv_edit_has_exp_{item_id}")
                        if has_exp:
                            try:
                                default_exp = date.fromisoformat(current_expiry) if current_expiry else date.today()
                            except (ValueError, TypeError):
                                default_exp = date.today()
                            edit_expiry = st.date_input("Expiry Date", value=default_exp, key=f"inv_edit_expiry_{item_id}")
                        else:
                            edit_expiry = None

                        edit_notes_input = st.text_area("Notes", value=display_notes, height=60, key=f"inv_edit_notes_{item_id}")
                        
                    with e_side:
                        st.markdown("##### 🖼️ Replace Image")
                        edit_uploaded = st.file_uploader("Upload new", type=["jpg", "jpeg", "png", "webp"], key=f"inv_edit_img_{item_id}")
                        if edit_uploaded:
                            st.image(edit_uploaded, caption="New Image Preview", use_container_width=True)
                        elif img_url:
                            st.image(img_url, caption="Current Image", use_container_width=True)

                    if st.button("💾 Save Changes", key=f"inv_save_{item_id}", use_container_width=True):
                        if not edit_name.strip():
                            st.error("Name cannot be empty.")
                        elif edit_qty < 0:
                            st.error("Quantity cannot be negative.")
                        else:
                            final_url = img_url
                            if edit_uploaded:
                                with st.spinner("Uploading new image..."):
                                    final_url = save_company_image(edit_uploaded)

                            # Re-encode image link inside updated text notes boundary footprint
                            updated_notes = edit_notes_input.strip()
                            if final_url:
                                updated_notes = f"{updated_notes} ||IMG:{final_url}".strip()

                            res = db.update_inventory_item(
                                item_id   = item_id,
                                user_id   = user_id,
                                item_name = edit_name.strip(),
                                category  = edit_category,
                                quantity  = float(edit_qty),
                                unit      = edit_unit,
                                supplier  = edit_supplier.strip() or None,
                                expiry_date = edit_expiry.isoformat() if edit_expiry else None,
                                notes     = updated_notes if updated_notes else None,
                            )
                            if res.get("success"):
                                st.success("✅ Item updated successfully.")
                                st.session_state[edit_key] = False
                                time.sleep(0.4)
                                st.rerun()
                            else:
                                st.error(f"❌ {res.get('error', 'Update failed.')}")

            # ── Delete Entry ──────────────────────────────────────────────────
            with action_cols[2]:
                del_confirm_key = f"inv_del_confirm_{item_id}"
                if not st.session_state.get(del_confirm_key, False):
                    if st.button("🗑️ Delete", key=f"inv_del_btn_{item_id}", use_container_width=True):
                        st.session_state[del_confirm_key] = True
                        st.rerun()
                else:
                    st.warning("Delete item?")
                    d1, d2 = st.columns(2)
                    with d1:
                        if st.button("Yes", key=f"inv_del_yes_{item_id}", use_container_width=True):
                            res = db.delete_inventory_item(item_id, user_id)
                            if res.get("success"):
                                st.success("Deleted.")
                                st.session_state[del_confirm_key] = False
                                time.sleep(0.3)
                                st.rerun()
                            else:
                                st.error(f"❌ {res.get('error')}")
                    with d2:
                        if st.button("No", key=f"inv_del_no_{item_id}", use_container_width=True):
                            st.session_state[del_confirm_key] = False
                            st.rerun()

        st.markdown("---")
    