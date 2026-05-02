import streamlit as st

st.set_page_config(
    page_title="Oracle Integration Copilot",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Oracle Integration Copilot")
st.caption(
    "Describe an Oracle Integration Cloud requirement in plain English. "
    "The copilot retrieves relevant OIC documentation and generates a complete design spec."
)

col_left, col_right = st.columns([2, 3], gap="large")

with col_left:
    requirement = st.text_area(
        "Integration Requirement",
        height=220,
        placeholder=(
            'e.g. "Every night at 2am, pull new hires from Workday and create employee '
            "records in Oracle HCM. Skip contractors. Send a Slack alert if any record fails.\""
        ),
    )

    with st.expander("Options", expanded=False):
        use_critic = st.checkbox("Critic review pass (surfaces hidden assumptions)", value=True)
        k = st.slider("Documents to retrieve", min_value=2, max_value=12, value=6, step=2)

    generate = st.button(
        "Generate Spec",
        type="primary",
        disabled=not requirement.strip(),
        use_container_width=True,
    )

with col_right:
    if generate and requirement.strip():
        with st.status("Generating integration spec …", expanded=True) as status:
            st.write("Parsing requirement …")
            try:
                from copilot.parser import parse_requirement
                intent = parse_requirement(requirement)
            except Exception as exc:
                status.update(label="Failed", state="error")
                st.error(f"Could not parse requirement: {exc}")
                st.stop()

            st.write(
                f"Pattern: **{intent.pattern}** | "
                f"**{intent.source_system}** → **{intent.target_system}**"
            )
            st.write("Retrieving Oracle documentation and designing spec …")

            try:
                from copilot.designer import design
                spec = design(intent, k=k, use_critic=use_critic)
            except Exception as exc:
                status.update(label="Failed", state="error")
                st.error(f"Could not generate spec: {exc}")
                st.stop()

            status.update(label="Done", state="complete", expanded=False)

        from copilot.renderers.markdown import render
        markdown_output = render(spec)

        st.download_button(
            label="Download as Markdown",
            data=markdown_output,
            file_name=f"{spec.title.lower().replace(' ', '_')[:60]}.md",
            mime="text/markdown",
        )

        st.divider()
        st.markdown(markdown_output)

    else:
        st.info(
            "Enter an integration requirement on the left and click **Generate Spec**.\n\n"
            "**Example requirements to try:**\n"
            "- *Sync new Workday hires to Oracle HCM every night at 2am. Skip contractors.*\n"
            "- *When a Coupa PO is approved, create a corresponding Oracle ERP Purchase Order.*\n"
            "- *Nightly sync of Salesforce closed-won opportunities to Oracle ERP as invoices.*"
        )
