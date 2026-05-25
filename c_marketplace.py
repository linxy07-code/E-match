import streamlit as st
import html as html_lib

from c_styles import COMPANY_CSS
from c_utils import _expiry_badge, _lt_badge


def render_company_marketplace(db, user_id):
    st.markdown(COMPANY_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="co-header">
        <h1>🏭 Company Marketplace</h1>
        <p>Browse inventory listed by other companies</p>
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns([2, 1, 1])

    search_q = f1.text_input(
        "Search",
        placeholder="🔍 Search products…",
        key="co_mp_search",
        label_visibility="collapsed"
    )

    filt_cat = f2.selectbox(
        "Category",
        ["All Categories","Groceries & Food","Household","Electronics",
         "Fashion & Apparel","Lifestyle & Hobbies","Others"],
        key="co_mp_cat"
    )

    filt_type = f3.selectbox(
        "Type",
        ["All Types","💵 Sell","🆓 Free","🔄 Exchange"],
        key="co_mp_type"
    )

    db_res = db.get_all_company_items(
        search=search_q if search_q else None,
        category=filt_cat if filt_cat != "All Categories" else None,
    )

    if not db_res.get("success"):
        st.error("Could not load company marketplace.")
        return

    items = db_res.get("items", [])
    items = [i for i in items if i.get("user_id") != user_id]

    type_map = {"💵 Sell": "sell", "🆓 Free": "free", "🔄 Exchange": "exchange"}
    if filt_type in type_map:
        items = [i for i in items if i.get("listing_type") == type_map[filt_type]]

    if not items:
        st.info("No company products found matching your filters.")
        return

    st.caption(f"{len(items)} product(s) found")

    for row_items in [items[i:i+3] for i in range(0, len(items), 3)]:
        cols_cards = st.columns(3)
        cols_buttons = st.columns(3)

        for col_idx, item in enumerate(row_items):
            item_id = item["item_id"]

            listing_type = item.get("listing_type") or "sell"
            price = item.get("price")

            exp_cls, exp_label = _expiry_badge(item.get("expiry_date"))
            badge_html = _lt_badge(listing_type, price)

            exp_badge = f'<span class="mp-badge {exp_cls}">{exp_label}</span>'

            raw_name = html_lib.escape(str(item.get("item_name", "")))
            company_name = html_lib.escape(
                str(item.get("company_name") or item.get("seller_name") or "—")
            )

            with cols_cards[col_idx]:
                img_url = item.get("image_path")

                if img_url:
                    st.markdown(f'<div class="co-mp-img-frame"><img src="{img_url}"></div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown("<div class='co-mp-img-frame'>🏭</div>",
                                unsafe_allow_html=True)

                st.markdown(f"""
                <div class="co-mp-card">
                    <p><b>{raw_name}</b></p>
                    <div>{badge_html} {exp_badge}</div>
                    <div>🏢 {company_name}</div>
                    <div>📍 {item.get('region','—')}</div>
                    <div>🏷️ {item.get('category','—')}</div>
                </div>
                """, unsafe_allow_html=True)

            with cols_buttons[col_idx]:
                btn_label = (
                    "🛍️ Request to Buy" if listing_type == "sell"
                    else "🔄 Offer Exchange" if listing_type == "exchange"
                    else "🙋 Claim Item"
                )

                with st.expander(btn_label):
                    msg_key = f"co_msg_{item_id}"

                    st.text_area("Message", key=msg_key, height=70)

                    if st.button("✅ Confirm", key=f"co_confirm_{item_id}"):
                        res = db.reserve_company_item(item_id, user_id)

                        if res.get("success"):
                            st.success("Reserved!")
                            st.rerun()
                        else:
                            st.error(res.get("error"))