# =================================================================================================== #
# Filename      : HMD_Great_Expectations_2026.py
# Purpose       : Great Expectations for Data Quality and Validation in Real-World Datasets.
#
#                 This tutorial covers basic concepts in Module 4: Data Quality and Validation in 
#                 Real-World Datasets. This script is designed for teaching. It demonstrates how 
#                 Great Expectations (GX) can operationalize the kinds of checks discussed in Module 4.
#
# Expectations  : 1. Schema enforcement
#                 2. Type checks
#                 3. Missingness / completeness checks
#                 4. Value-range checks
#                 5. Duplicate detection / uniqueness checks
#                 6. Controlled vocabulary checks
#                 7. Business-rule validation
#                 8. Expectation Suites and reusable validation workflows
#
# Commands      : conda install conda-forge::pandas
#                 conda install conda-forge::great-expectations OR
#                 pip install great-expectations AND
#                 pip install --upgrade great_expectations (this is important)
#
#                 To run this code, type >> python HMD_Great_Expectations_2026.py
#
# Remarks       : The script builds a small synthetic orders dataset with deliberate quality issues. 
#                 It uses the current GX Core style with an in-memory pandas DataFrame, an
#                 ephemeral Data Context, a Data Source, a Data Asset, a Batch Definition, and
#                 an Expectation Suite.
#                 The goal is clarity and teachability rather than production hardening. 
#
# Composer      : Dr. Hassan Mohy-ud-Din (hassan.mohyuddin@lums.edu.pk)
# Date          : March 14, 2026 (update and/or last successful run)
# =================================================================================================== #

from __future__                 import annotations

import json
import numpy                    as np
import pandas                   as pd


from pathlib                    import Path
from typing                     import Any, Dict, List

try:
                                import great_expectations                       as gx
except ImportError as exc:
    raise SystemExit("Great Expectations is not installed.\n"
                     "Install it with: pip install great_expectations pandas numpy") from exc

# =================================================================================================== #
# 1. Build a small dataset with intentionally injected data-quality issues.
def build_demo_orders_dataframe() -> pd.DataFrame:
    """
    Create a small orders table with both valid and invalid rows.
    The injected issues are deliberate so that students can see Great Expectations
    catching them:
    - duplicate order_id
    - missing customer_id
    - invalid status category
    - out-of-range numeric values
    - business-rule violations (ship_date before order_date, bad line total)
    - one suspect type decision for demonstration (quantity stored as float)
    """
    df = pd.DataFrame(
        {
            "order_id"      : [1001, 1002, 1003, 1003, 1005, 1006, 1007, 1008],
            "customer_id"   : ["C001", "C002", "C003", "C004", None, "C006", "C007", "C008"],
            "order_date"    : ["2026-02-01",
                               "2026-02-01",
                               "2026-02-02",
                               "2026-02-03",
                               "2026-02-03",
                               "2026-02-04",
                               "2026-02-05",
                               "2026-02-05",],
            "ship_date"     : ["2026-02-02",
                               "2026-02-02",
                               "2026-02-01",                # invalid: ships before order date
                               "2026-02-05",
                               "2026-02-04",
                               "2026-02-04",
                               "2026-02-06",
                               "2026-02-06",],
            "status"        : ["PLACED",
                               "SHIPPED",
                               "DELIVERED",
                               "RETURNED",
                               "UNKNOWN",                   # invalid category
                               "SHIPPED",
                               "DELIVERED",
                               "PLACED",],
            
            # Stored as float here to keep arithmetic easy, while also allowing
            # a type expectation to demonstrate float-vs-int style discussions.
            "quantity"      : [2.0, 1.0, -3.0, 4.0, 2.0, 1.0, 3.0, 2.0],                    # -3 is invalid
            "unit_price"    : [120.0, 80.0, 50.0, 35.0, 5000.0, 95.0, 60.0, 75.0],          # 5000 is suspicious
            "discount_rate" : [0.10, 0.00, 0.05, 0.20, 1.20, 0.15, 0.00, 0.50],             # 1.20 is invalid
            "line_total"    : [240.0, 80.0, -150.0, 140.0, 100.0, 95.0, 180.0, 999.0],      # row 8 wrong total
            "country_code"  : ["PK", "PK", "US", "US", "PAK", "AE", "GB", "PK"],            # PAK invalid if ISO-2 expected
            "email"         : ["a@example.com",
                               "b@example.com",
                               "c@example.com",
                               "d@example.com",
                               None,
                               "f@example.com",
                               "g@example.com",
                               "h@example.com",],
        }
    )

    # This code creates derived audit columns used to check whether certain business rules 
    # are satisfied in a dataset using pandas and NumPy.
    # - Converts the columns order_date and ship_date into proper datetime objects.
    # - errors = "coerce" converts invalid values to NaT (missing date) instead of raising an error.
    # It ensures date comparisons can be performed safely.
    order_dt                        = pd.to_datetime(df["order_date"]   , errors = "coerce")
    ship_dt                         = pd.to_datetime(df["ship_date"]    , errors = "coerce")

    # Validate shipping happens after ordering.
    # Creates a boolean audit column indicating whether the business rule is satisfied.
    # The rule is True only if: 
    #                           (1) Order date exists, 
    #                           (2) Ship date exists, and
    #                           (3) Ship date is on or after the order date.
    df["shipping_after_order_rule"] = (order_dt.notna() & ship_dt.notna() & (ship_dt >= order_dt))

    # Compute expected line total. 
    # Calculates what the line total should be using the pricing formula:
    # expected_total = quantity × unit_price × (1 − discount_rate).
    expected_total                  = df["quantity"] * df["unit_price"] * (1.0 - df["discount_rate"])

    # Check if recorded total matches the computed value.
    # Creates another boolean validation column that checks whether the stored line_total is 
    # numerically close to the computed value.
    df["line_total_matches_rule"]   = np.isclose(df["line_total"], expected_total, atol = 1e-6)

    return df

# =================================================================================================== #
# 2. Set up Great Expectations on an in-memory pandas DataFrame.
def build_batch_from_dataframe(df: pd.DataFrame):
    """
    Create an ephemeral GX context and connect the pandas DataFrame as a Batch.
    This mirrors the current GX Core workflow for dataframe data.

    Remarks: In the ephemeral GX context of Great Expectations, ephemeral means temporary and in-memory, 
             without being saved as a persistent project or configuration on disk. In an ephemeral 
             workflow, validations are created and executed programmatically within a script or notebook, 
             often on a pandas DataFrame, and the configuration (datasource, expectations, validator) 
             exists only for that session. In short, ephemeral GX is used for quick, lightweight 
             validations during exploration, testing, or pipelines, where you do not need a full 
             persisted GX project structure.
    """
    # Creates a Great Expectations context. 
    # A context is the main object that manages:
    #                                           - datasources
    #                                           - data assets
    #                                           - validation configurations
    #                                           - expectations
    # Since no project folder is loaded, this becomes an ephemeral context (temporary and in-memory).
    context             = gx.get_context()

    # Registers a pandas datasource inside GX. A datasource tells GX where the data comes from.
    data_source         = context.data_sources.add_pandas(name = "module4_pandas_source")

    # Defines a data asset. A data asset represents a logical dataset inside the datasource.
    # Example meanings of assets:
    #                           - orders
    #                           - transactions
    #                           - customer_records
    # Here the asset represents the orders DataFrame.
    data_asset          = data_source.add_dataframe_asset(name = "orders_dataframe_asset")
    
    # Defines how batches of data will be created. A Batch in GX is: the specific slice of data 
    # that will be validated.
    batch_definition    = data_asset.add_batch_definition_whole_dataframe("whole_orders_dataframe")
    
    # This step attaches the actual pandas DataFrame to the GX batch.
    # GX now knows:
    #               - which dataframe to validate,
    #               - which asset it belongs to,
    #               - which datasource it came from.
    batch               = batch_definition.get_batch(batch_parameters = {"dataframe": df})

    return context, batch_definition, batch

# =================================================================================================== #
# 3. Define expectations that map directly to Module 4 lecture themes.
def build_expectations() -> List[Any]:
    """
    Build a list of Expectations. The list intentionally mixes:
    - hard/critical constraints
    - softer warning-level checks

    Remarks: This helps students see that not every data-quality rule has the same operational severity.
    """
    expectations: List[Any] = [
                                # Schema enforcement
                                gx.expectations.ExpectColumnToExist(column = "order_id"     , severity = "critical",),
                                gx.expectations.ExpectColumnToExist(column = "customer_id"  , severity = "critical",),
                                gx.expectations.ExpectColumnToExist(column = "status"       , severity = "critical",),

                                # Type checks
                                gx.expectations.ExpectColumnValuesToBeOfType(column     = "line_total", 
                                                                             type_      = "float64",
                                                                             severity   = "warning",),

                                # Completeness / missingness
                                gx.expectations.ExpectColumnValuesToNotBeNull(column    = "customer_id",
                                                                              mostly    = 0.95,
                                                                              severity  = "critical",),
                                gx.expectations.ExpectColumnValuesToNotBeNull(column    = "email",
                                                                              mostly    = 0.85,
                                                                              severity  = "warning",),

                                # Uniqueness / duplicate detection
                                gx.expectations.ExpectColumnValuesToBeUnique(column     = "order_id",
                                                                             severity   = "critical",),

                                # Value-range checks
                                gx.expectations.ExpectColumnValuesToBeBetween(column    = "quantity",
                                                                              min_value = 1,
                                                                              max_value = 20,
                                                                              severity  = "critical",),
                                gx.expectations.ExpectColumnValuesToBeBetween(column    = "unit_price",
                                                                              min_value = 0,
                                                                              max_value = 1000,
                                                                              severity  = "warning",),
                                gx.expectations.ExpectColumnValuesToBeBetween(column    = "discount_rate",
                                                                              min_value = 0,
                                                                              max_value = 1,
                                                                              severity  = "critical",),
                                gx.expectations.ExpectTableRowCountToBeBetween(min_value= 5,
                                                                               max_value= 1000,
                                                                               severity = "warning",),

                                # Controlled vocabulary / categorical integrity
                                gx.expectations.ExpectColumnValuesToBeInSet(column      = "status",
                                                                            value_set   = ["PLACED", "SHIPPED", "DELIVERED", "RETURNED"],
                                                                            severity    = "critical",),
                                gx.expectations.ExpectColumnValuesToBeInSet(column      = "country_code",
                                                                            value_set   = ["PK", "US", "GB", "AE"],
                                                                            severity    = "warning",),

                                # Domain / business-rule validation
                                # A practical pattern: compute a boolean audit column in pandas,
                                # then require that the boolean is always True.
                                gx.expectations.ExpectColumnValuesToBeInSet(column      = "shipping_after_order_rule",
                                                                            value_set   = [True],
                                                                            severity    = "critical",),
                                gx.expectations.ExpectColumnValuesToBeInSet(column      = "line_total_matches_rule",
                                                                            value_set   = [True],
                                                                            severity    = "critical",),]
    return expectations

# =================================================================================================== #
# 4. Helpers for serializing and reporting validation results.
def gx_result_to_dict(result: Any) -> Dict[str, Any]:
    """
    This function converts a validation result object (often returned by Great Expectations) into a 
    standard Python dictionary so it can be easily serialized, logged, saved to JSON, or reported. 
    It is designed to be robust and compatible with multiple object formats.
    """
    # Checks whether the result is already a dictionary. If Yes, no conversion needed.
    if isinstance(result, dict): return result
    
    # The function checks if the object has any of these methods.
    for method_name in ("to_json_dict", "as_dict", "model_dump"):
        method  = getattr(result, method_name, None)
        if callable(method):
            try:
                converted = method()
                if isinstance(converted, dict):
                    return converted
            except Exception:
                pass
    
    # Try JSON string methods
    for method_name in ("to_json", "model_dump_json", "json"):
        method  = getattr(result, method_name, None)
        if callable(method):
            try:
                # Convert JSON string into dictionary
                raw = method()
                if isinstance(raw, str):
                    return json.loads(raw)
            except Exception:
                pass

    # Try direct dictionary casting            
    try:
        return dict(result)
    except Exception:
        # Last fallback - if everything fails - This stores the string representation of the object.
        return {"repr": repr(result)}

# =================================================================================================== #
def summarize_single_expectation_result(result_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    This function extracts a small, readable summary from a single validation result produced by 
    Great Expectations. Instead of returning the full verbose validation output, it keeps only the most 
    useful fields for reporting or dashboards.
    """
    # Extract configuration information.
    config  = result_dict.get("expectation_config", {})

    # This retrieves the actual validation output produced by GX.
    res     = result_dict.get("result", {})

    # The function returns a new dictionary containing selected fields:
    return {"expectation_type"          : config.get("type") or config.get("expectation_type", "unknown"),
            "success"                   : result_dict.get("success"),
            "unexpected_count"          : res.get("unexpected_count"),
            "unexpected_percent"        : res.get("unexpected_percent"),
            "partial_unexpected_list"   : res.get("partial_unexpected_list", []),}

# =================================================================================================== #
def print_section(title: str) -> None:
    """
    This is a simple helper function for printing section headers in console output or notebooks, 
    making logs or reports more readable.
    """
    print("\n" + "=" * 88)              # Print a top border
    print(title)                        # Print the title
    print("=" * 88)                     # Print a bottom border

# =================================================================================================== #
# 5. Main tutorial workflow.
def main() -> None:
    output_dir      = Path("module4_gx_outputs")
    output_dir.mkdir(exist_ok=True)

    #--------------------------------------------------------------#
    print_section("STEP 1 - Build a messy real-world style dataset")
    #--------------------------------------------------------------#

    df              = build_demo_orders_dataframe()
    print(df)

    raw_csv_path    = output_dir / "demo_orders.csv"
    df.to_csv(raw_csv_path, index=False)
    print(f"\nSaved demo dataset to: {raw_csv_path.resolve()}")

    #-----------------------------------------------------------------------------------------#
    print_section("STEP 2 - Create GX context, datasource, asset, batch definition, and batch")
    #-----------------------------------------------------------------------------------------#

    context, batch_definition, batch = build_batch_from_dataframe(df)
    
    print(f"GX version: {getattr(gx, '__version__', 'unknown')}")
    print(f"Context type: {type(context).__name__}")
    print("Batch created successfully.")

    #-----------------------------------------------------------------#
    print_section("STEP 3 - Define expectations aligned with Module 4")
    #-----------------------------------------------------------------#
    expectations    = build_expectations()
    print(f"Number of expectations defined: {len(expectations)}")
    
    for idx, expectation in enumerate(expectations, start=1):
        print(f"{idx:02d}. {type(expectation).__name__}")

    #------------------------------------------------------------------------#
    print_section("STEP 4 - Run ad hoc validations one expectation at a time")
    #------------------------------------------------------------------------#

    summaries: List[Dict[str, Any]] = []
    for expectation in expectations:
        result      = batch.validate(expectation)
        result_dict = gx_result_to_dict(result)
        summary     = summarize_single_expectation_result(result_dict)
        summaries.append(summary)

        print(f"\nExpectation   : {summary['expectation_type']}")
        print(f"Success         : {summary['success']}")
        print(f"Unexpected      : {summary['unexpected_count']}")
        
        if summary["partial_unexpected_list"]:
            print(f"Examples    : {summary['partial_unexpected_list']}")

    summary_df          = pd.DataFrame(summaries)
    summary_csv_path    = output_dir / "ad_hoc_validation_summary.csv"
    summary_df.to_csv(summary_csv_path, index=False)

    print("\nCompact validation summary:")
    print(summary_df)
    print(f"\nSaved summary to: {summary_csv_path.resolve()}")

    #-----------------------------------------------------------------------#
    print_section("STEP 5 - Organize expectations into an Expectation Suite")
    #-----------------------------------------------------------------------#

    suite           = gx.ExpectationSuite(name="module4_orders_expectation_suite")
    suite           = context.suites.add(suite)

    for expectation in expectations: suite.add_expectation(expectation)

    print(f"Expectation Suite name  : {suite.name}")
    print(f"Expectations in suite   :  {len(suite.expectations)}")

    #-----------------------------------------------------------------------------------#
    print_section("STEP 6 - Create a Validation Definition and validate the whole suite")
    #-----------------------------------------------------------------------------------#

    validation_definition = context.validation_definitions.add(
        gx.core.validation_definition.ValidationDefinition(name = "module4_orders_validation",
                                                           data = batch_definition,
                                                           suite= suite,))

    suite_result        = validation_definition.run(batch_parameters={"dataframe": df})
    suite_result_dict   = gx_result_to_dict(suite_result)

    suite_result_path   = output_dir / "suite_validation_result.json"
    with suite_result_path.open("w", encoding="utf-8") as f:
        json.dump(suite_result_dict, f, indent=2, default=str)

    print("Full suite validation finished.")
    print(f"Saved suite result JSON to: {suite_result_path.resolve()}")

    #---------------------------------------#
    print_section("STEP 7 - Teaching notes")
    #---------------------------------------#

    print("""
          What this tutorial demonstrates
          -------------------------------
          1. GX converts informal quality expectations into executable tests.
          2. A dataframe can be validated in-memory during teaching, prototyping, or CI.
          3. Expectation Suites let you group many checks into a reusable data contract.
          4. Domain rules often become easiest to validate after creating boolean audit columns.
          5. Validation should happen before data is trusted downstream for analytics or ML.

          Suggested classroom extensions
          ------------------------------
          - Add a new column and create a schema check for it.
          - Change the allowed status values and re-run the suite.
          - Tighten or relax `mostly=` thresholds and discuss tolerance.
          - Add a partition/date freshness check outside the dataframe example.
          - Compare GX validation with ydata-profiling: rules vs descriptive summaries.
          """.strip())

    print_section("DONE")
    print("Artifacts created in the local folder: module4_gx_outputs/")

# =================================================================================================== #
if __name__ == "__main__":
    main()

# =================================================================================================== #