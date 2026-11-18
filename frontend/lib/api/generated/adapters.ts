/** Generated from adapters.openapi.json. Run npm run generate:adapter-types; do not edit. */
export interface paths {
    "/api/companies/{company_id}/source-adapters/documents/{document_id}/extract": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Document Extract */
        post: operations["document_extract_api_companies__company_id__source_adapters_documents__document_id__extract_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/companies/{company_id}/source-adapters/india-filings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** India Filings */
        post: operations["india_filings_api_companies__company_id__source_adapters_india_filings_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/companies/{company_id}/source-adapters/sec-facts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Sec Facts */
        post: operations["sec_facts_api_companies__company_id__source_adapters_sec_facts_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/companies/{company_id}/source-adapters/transcript": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Transcript */
        post: operations["transcript_api_companies__company_id__source_adapters_transcript_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/data-adapters/{provider}/corporate-actions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Adapter Actions */
        post: operations["adapter_actions_api_data_adapters__provider__corporate_actions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/data-adapters/{provider}/dated-quote": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Adapter Dated Quote */
        post: operations["adapter_dated_quote_api_data_adapters__provider__dated_quote_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/data-adapters/{provider}/history": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Adapter History */
        post: operations["adapter_history_api_data_adapters__provider__history_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/data-adapters/{provider}/quote": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Adapter Quote */
        post: operations["adapter_quote_api_data_adapters__provider__quote_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/data-adapters/{provider}/reference": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Adapter Reference */
        post: operations["adapter_reference_api_data_adapters__provider__reference_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/data-adapters/calendars/schedule": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Adapter Calendar */
        post: operations["adapter_calendar_api_data_adapters_calendars_schedule_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/data-adapters/identity/openfigi": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Adapter Identity */
        post: operations["adapter_identity_api_data_adapters_identity_openfigi_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research-lab/allocation": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Allocation */
        post: operations["allocation_api_research_lab_allocation_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research-lab/capabilities": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Research Capabilities */
        get: operations["research_capabilities_api_research_lab_capabilities_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research-lab/peers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Peers */
        post: operations["peers_api_research_lab_peers_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research-lab/report": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Report */
        post: operations["report_api_research_lab_report_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research-lab/runs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Runs */
        get: operations["runs_api_research_lab_runs_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research-lab/runs/{run_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Run */
        get: operations["run_api_research_lab_runs__run_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research-lab/runs/{run_id}/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Export */
        get: operations["export_api_research_lab_runs__run_id__export_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research-lab/runs/{run_id}/report.html": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Html Report */
        get: operations["html_report_api_research_lab_runs__run_id__report_html_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research-lab/simulation": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Simulation */
        post: operations["simulation_api_research_lab_simulation_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/source-adapters": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Source Capabilities */
        get: operations["source_capabilities_api_source_adapters_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/source-adapters/fred-vintage": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Fred Vintage */
        post: operations["fred_vintage_api_source_adapters_fred_vintage_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AdapterActionRequest */
        AdapterActionRequest: {
            /** Currency */
            currency?: string | null;
            /**
             * End Date
             * Format: date
             */
            end_date: string;
            /** Exchange */
            exchange?: string | null;
            /** Market */
            market: string;
            /**
             * Start Date
             * Format: date
             */
            start_date: string;
            /** Ticker */
            ticker: string;
        };
        /** AdapterActionsResult */
        AdapterActionsResult: {
            /** Actions */
            actions?: components["schemas"]["CorporateActionEvidence"][];
            /**
             * Coverage
             * @enum {string}
             */
            coverage: "complete" | "partial" | "empty";
            /** Gaps */
            gaps?: components["schemas"]["AdapterCoverageGap"][];
            /** Warnings */
            warnings?: string[];
        };
        /** AdapterCapability */
        AdapterCapability: {
            /** Available */
            available: boolean;
            /** Id */
            id: string;
            /** Label */
            label: string;
            /** Reason */
            reason?: string | null;
            /** Version */
            version?: string | null;
        };
        /** AdapterCoverageGap */
        AdapterCoverageGap: {
            /** Code */
            code: string;
            /** End Date */
            end_date?: string | null;
            /**
             * Retryable
             * @default false
             */
            retryable?: boolean;
            /** Start Date */
            start_date?: string | null;
        };
        /** AdapterDatedQuoteRequest */
        AdapterDatedQuoteRequest: {
            /** Currency */
            currency?: string | null;
            /** Exchange */
            exchange?: string | null;
            /** Market */
            market: string;
            /**
             * Requested Date
             * Format: date
             */
            requested_date: string;
            /** Ticker */
            ticker: string;
        };
        /** AdapterDatedQuoteResult */
        AdapterDatedQuoteResult: {
            /**
             * Actual Date
             * Format: date
             */
            actual_date: string;
            point: components["schemas"]["MarketHistoryResult"];
            /**
             * Previous Session Substitution
             * @default false
             */
            previous_session_substitution?: boolean;
            /**
             * Requested Date
             * Format: date
             */
            requested_date: string;
        };
        /**
         * AdapterHistoryRequest
         * @description Inclusive dates; distinct from the legacy trailing-days request.
         */
        AdapterHistoryRequest: {
            /**
             * Adjustment
             * @default provider
             * @enum {string}
             */
            adjustment?: "provider" | "unadjusted" | "split_adjusted";
            /** Currency */
            currency?: string | null;
            /**
             * End Date
             * Format: date
             */
            end_date: string;
            /** Exchange */
            exchange?: string | null;
            /** Market */
            market: string;
            /**
             * Start Date
             * Format: date
             */
            start_date: string;
            /** Ticker */
            ticker: string;
        };
        /** AdapterHistoryResult */
        AdapterHistoryResult: {
            /**
             * Coverage
             * @enum {string}
             */
            coverage: "complete" | "partial" | "empty";
            /** Gaps */
            gaps?: components["schemas"]["AdapterCoverageGap"][];
            /** Points */
            points?: components["schemas"]["MarketHistoryResult"][];
            /**
             * Requested End
             * Format: date
             */
            requested_end: string;
            /**
             * Requested Start
             * Format: date
             */
            requested_start: string;
            /** Warnings */
            warnings?: string[];
        };
        /** AllocationRequest */
        AllocationRequest: {
            /** Annual Expected Returns */
            annual_expected_returns?: {
                [key: string]: number;
            } | null;
            /** Baseline Weights */
            baseline_weights?: {
                [key: string]: number;
            } | null;
            /**
             * Covariance
             * @default ledoit_wolf
             * @enum {string}
             */
            covariance?: "ledoit_wolf" | "sample";
            dataset: components["schemas"]["ResearchDataset"];
            /** Groups */
            groups?: components["schemas"]["GroupConstraint"][];
            /** Max Turnover */
            max_turnover?: number | null;
            /**
             * Max Weight
             * @default 1
             */
            max_weight?: number;
            /**
             * Min Weight
             * @default 0
             */
            min_weight?: number;
            /**
             * Objective
             * @default min_volatility
             * @enum {string}
             */
            objective?: "min_volatility" | "max_sharpe" | "hrp" | "equal_weight";
            /**
             * Risk Free Rate
             * @default 0.04
             */
            risk_free_rate?: number;
        };
        /** ApiErrorDetail */
        ApiErrorDetail: {
            /** Code */
            code: string;
            /** Field */
            field?: string | null;
            /** Message */
            message: string;
            /** Processing Run Id */
            processing_run_id?: number | null;
            /** Provider */
            provider?: string | null;
            /**
             * Retryable
             * @default false
             */
            retryable?: boolean;
            /** Target */
            target?: string | null;
        };
        /** ApiMeta */
        ApiMeta: {
            /**
             * Confidence
             * @default medium
             */
            confidence?: string;
            /**
             * Is Mock
             * @default false
             */
            is_mock?: boolean;
            /**
             * Is Stale
             * @default false
             */
            is_stale?: boolean;
            /** Last Updated */
            last_updated?: string | null;
            /** Processing Time Ms */
            processing_time_ms?: number | null;
            /** Request Id */
            request_id?: string | null;
            /**
             * Source
             * @default internal
             */
            source?: string;
            /**
             * Status
             * @default success
             */
            status?: string;
            /** Warnings */
            warnings?: string[];
        };
        /** ApiResponse[DataAdapterReceipt[AdapterActionsResult]] */
        ApiResponse_DataAdapterReceipt_AdapterActionsResult__: {
            data?: components["schemas"]["DataAdapterReceipt_AdapterActionsResult_"] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** ApiResponse[DataAdapterReceipt[AdapterDatedQuoteResult]] */
        ApiResponse_DataAdapterReceipt_AdapterDatedQuoteResult__: {
            data?: components["schemas"]["DataAdapterReceipt_AdapterDatedQuoteResult_"] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** ApiResponse[DataAdapterReceipt[AdapterHistoryResult]] */
        ApiResponse_DataAdapterReceipt_AdapterHistoryResult__: {
            data?: components["schemas"]["DataAdapterReceipt_AdapterHistoryResult_"] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** ApiResponse[DataAdapterReceipt[CalendarScheduleResult]] */
        ApiResponse_DataAdapterReceipt_CalendarScheduleResult__: {
            data?: components["schemas"]["DataAdapterReceipt_CalendarScheduleResult_"] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** ApiResponse[DataAdapterReceipt[IdentityMappingResult]] */
        ApiResponse_DataAdapterReceipt_IdentityMappingResult__: {
            data?: components["schemas"]["DataAdapterReceipt_IdentityMappingResult_"] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** ApiResponse[DataAdapterReceipt[MarketQuoteResult]] */
        ApiResponse_DataAdapterReceipt_MarketQuoteResult__: {
            data?: components["schemas"]["DataAdapterReceipt_MarketQuoteResult_"] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** ApiResponse[DataAdapterReceipt[SecurityReferenceResult]] */
        ApiResponse_DataAdapterReceipt_SecurityReferenceResult__: {
            data?: components["schemas"]["DataAdapterReceipt_SecurityReferenceResult_"] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** ApiResponse[list[ResearchRunSummary]] */
        ApiResponse_list_ResearchRunSummary__: {
            /** Data */
            data?: components["schemas"]["ResearchRunSummary"][] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** ApiResponse[list[SourceAdapterCapability]] */
        ApiResponse_list_SourceAdapterCapability__: {
            /** Data */
            data?: components["schemas"]["SourceAdapterCapability"][] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** ApiResponse[ResearchCapabilities] */
        ApiResponse_ResearchCapabilities_: {
            data?: components["schemas"]["ResearchCapabilities"] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** ApiResponse[ResearchRunResult] */
        ApiResponse_ResearchRunResult_: {
            data?: components["schemas"]["ResearchRunResult"] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** ApiResponse[SourceAdapterResult] */
        ApiResponse_SourceAdapterResult_: {
            data?: components["schemas"]["SourceAdapterResult"] | null;
            /** Errors */
            errors?: components["schemas"]["ApiErrorDetail"][];
            meta?: components["schemas"]["ApiMeta"];
        };
        /** CalendarScheduleRequest */
        CalendarScheduleRequest: {
            /**
             * End Date
             * Format: date
             */
            end_date: string;
            /**
             * Exchange
             * @enum {string}
             */
            exchange: "XNYS" | "XNAS" | "XNSE" | "XBOM";
            /** Overrides */
            overrides?: components["schemas"]["CalendarSessionOverride"][];
            /**
             * Start Date
             * Format: date
             */
            start_date: string;
        };
        /** CalendarScheduleResult */
        CalendarScheduleResult: {
            /**
             * Coverage End
             * Format: date
             */
            coverage_end: string;
            /**
             * Coverage Start
             * Format: date
             */
            coverage_start: string;
            /** Exchange */
            exchange: string;
            /** Library Version */
            library_version: string;
            /** Override Hash */
            override_hash: string;
            /** Sessions */
            sessions: components["schemas"]["CalendarSession"][];
            /** Timezone */
            timezone: string;
            /** Warnings */
            warnings: string[];
        };
        /** CalendarSession */
        CalendarSession: {
            /**
             * Closes At
             * Format: date-time
             */
            closes_at: string;
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Interruptions */
            interruptions?: [
                string,
                string
            ][];
            /**
             * Opens At
             * Format: date-time
             */
            opens_at: string;
            /**
             * Source
             * @default library
             * @enum {string}
             */
            source?: "library" | "user_source_override";
            /** Source Url */
            source_url?: string | null;
        };
        /** CalendarSessionOverride */
        CalendarSessionOverride: {
            /**
             * Closed
             * @default false
             */
            closed?: boolean;
            /** Closes At */
            closes_at?: string | null;
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Opens At */
            opens_at?: string | null;
            /** Reason */
            reason: string;
            /** Source Url */
            source_url: string;
        };
        /** CorporateActionEvidence */
        CorporateActionEvidence: {
            /**
             * Action Type
             * @enum {string}
             */
            action_type: "split" | "bonus" | "dividend" | "other";
            /** Announcement Date */
            announcement_date?: string | null;
            /** Cash Amount */
            cash_amount?: string | null;
            /** Currency */
            currency?: string | null;
            /** Description */
            description: string;
            /** Ex Date */
            ex_date?: string | null;
            /** Exchange */
            exchange?: string | null;
            /** Execution Date */
            execution_date?: string | null;
            /** Market */
            market: string;
            /** New Shares */
            new_shares?: string | null;
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Old Shares */
            old_shares?: string | null;
            /** Payment Date */
            payment_date?: string | null;
            /** Provider */
            provider: string;
            /** Provider Record Id */
            provider_record_id?: string | null;
            /** Publication Time */
            publication_time?: string | null;
            /** Record Date */
            record_date?: string | null;
            /** Source Locator */
            source_locator: string;
            /** Source Response Hash */
            source_response_hash: string;
            /** Ticker */
            ticker: string;
            /** Warnings */
            warnings?: string[];
        };
        /** DataAdapterReceipt[AdapterActionsResult] */
        DataAdapterReceipt_AdapterActionsResult_: {
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Processing Run Id */
            processing_run_id: number;
            /** Provider */
            provider: string;
            result: components["schemas"]["AdapterActionsResult"];
            /** Source Document Ids */
            source_document_ids?: number[];
            /** Warnings */
            warnings?: string[];
        };
        /** DataAdapterReceipt[AdapterDatedQuoteResult] */
        DataAdapterReceipt_AdapterDatedQuoteResult_: {
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Processing Run Id */
            processing_run_id: number;
            /** Provider */
            provider: string;
            result: components["schemas"]["AdapterDatedQuoteResult"];
            /** Source Document Ids */
            source_document_ids?: number[];
            /** Warnings */
            warnings?: string[];
        };
        /** DataAdapterReceipt[AdapterHistoryResult] */
        DataAdapterReceipt_AdapterHistoryResult_: {
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Processing Run Id */
            processing_run_id: number;
            /** Provider */
            provider: string;
            result: components["schemas"]["AdapterHistoryResult"];
            /** Source Document Ids */
            source_document_ids?: number[];
            /** Warnings */
            warnings?: string[];
        };
        /** DataAdapterReceipt[CalendarScheduleResult] */
        DataAdapterReceipt_CalendarScheduleResult_: {
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Processing Run Id */
            processing_run_id: number;
            /** Provider */
            provider: string;
            result: components["schemas"]["CalendarScheduleResult"];
            /** Source Document Ids */
            source_document_ids?: number[];
            /** Warnings */
            warnings?: string[];
        };
        /** DataAdapterReceipt[IdentityMappingResult] */
        DataAdapterReceipt_IdentityMappingResult_: {
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Processing Run Id */
            processing_run_id: number;
            /** Provider */
            provider: string;
            result: components["schemas"]["IdentityMappingResult"];
            /** Source Document Ids */
            source_document_ids?: number[];
            /** Warnings */
            warnings?: string[];
        };
        /** DataAdapterReceipt[MarketQuoteResult] */
        DataAdapterReceipt_MarketQuoteResult_: {
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Processing Run Id */
            processing_run_id: number;
            /** Provider */
            provider: string;
            result: components["schemas"]["MarketQuoteResult"];
            /** Source Document Ids */
            source_document_ids?: number[];
            /** Warnings */
            warnings?: string[];
        };
        /** DataAdapterReceipt[SecurityReferenceResult] */
        DataAdapterReceipt_SecurityReferenceResult_: {
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Processing Run Id */
            processing_run_id: number;
            /** Provider */
            provider: string;
            result: components["schemas"]["SecurityReferenceResult"];
            /** Source Document Ids */
            source_document_ids?: number[];
            /** Warnings */
            warnings?: string[];
        };
        /** DocumentExtractionRequest */
        DocumentExtractionRequest: {
            /**
             * Adapter
             * @enum {string}
             */
            adapter: "camelot" | "docling" | "marker";
            /** Pages */
            pages: number[];
        };
        /** FredVintageRequest */
        FredVintageRequest: {
            /**
             * As Of
             * Format: date
             */
            as_of: string;
            /**
             * Max Pages
             * @default 5
             */
            max_pages?: number;
            /**
             * Mode
             * @default as_of
             * @enum {string}
             */
            mode?: "as_of" | "initial_release";
            /**
             * Observation End
             * Format: date
             */
            observation_end: string;
            /**
             * Observation Start
             * Format: date
             */
            observation_start: string;
            /** Series Id */
            series_id: string;
        };
        /** GroupConstraint */
        GroupConstraint: {
            /**
             * Max Weight
             * @default 1
             */
            max_weight?: number;
            /** Members */
            members: string[];
            /**
             * Min Weight
             * @default 0
             */
            min_weight?: number;
            /** Name */
            name: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** IdentityCandidate */
        IdentityCandidate: {
            /** Composite Figi */
            composite_figi?: string | null;
            /** Exchange Code */
            exchange_code?: string | null;
            /** Figi */
            figi: string;
            /** Market Sector */
            market_sector?: string | null;
            /** Name */
            name?: string | null;
            /** Security Type */
            security_type?: string | null;
            /** Share Class Figi */
            share_class_figi?: string | null;
            /** Ticker */
            ticker?: string | null;
        };
        /** IdentityMappingRequest */
        IdentityMappingRequest: {
            /** Exchange Code */
            exchange_code?: string | null;
            /**
             * Id Type
             * @enum {string}
             */
            id_type: "TICKER" | "ID_ISIN" | "ID_CUSIP" | "ID_SEDOL" | "ID_BB_GLOBAL";
            /** Id Value */
            id_value: string;
            /**
             * Include Unlisted Equities
             * @default false
             */
            include_unlisted_equities?: boolean;
            /** Mic Code */
            mic_code?: string | null;
        };
        /** IdentityMappingResult */
        IdentityMappingResult: {
            /** Candidates */
            candidates: components["schemas"]["IdentityCandidate"][];
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /**
             * Resolution
             * @enum {string}
             */
            resolution: "candidate" | "ambiguous" | "unresolved";
            /** Warnings */
            warnings?: string[];
        };
        /** IndiaFilingsRequest */
        IndiaFilingsRequest: {
            /**
             * Exchange
             * @enum {string}
             */
            exchange: "NSE" | "BSE";
            /** Records */
            records: {
                [key: string]: unknown;
            }[];
        };
        /** MarketDataRequest */
        MarketDataRequest: {
            /** Currency */
            currency?: string | null;
            /** Exchange */
            exchange?: string | null;
            /** Market */
            market: string;
            /** Ticker */
            ticker: string;
        };
        /** MarketHistoryResult */
        MarketHistoryResult: {
            /**
             * Adjustment State
             * @default unknown
             * @enum {string}
             */
            adjustment_state?: "adjusted" | "unadjusted" | "not_applicable" | "unknown";
            /** Close Price */
            close_price: string;
            /** Currency */
            currency: string;
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Exchange */
            exchange?: string | null;
            /** Market */
            market: string;
            /**
             * Observed At
             * Format: date-time
             */
            observed_at?: string;
            /**
             * Price Type
             * @default end_of_day
             * @enum {string}
             */
            price_type?: "real_time" | "delayed" | "end_of_day" | "unknown" | "manual";
            /** Provider Name */
            provider_name: string;
            /** Provider Symbol */
            provider_symbol: string;
            /** Ticker */
            ticker: string;
            /** Warnings */
            warnings?: string[];
        };
        /** MarketQuoteResult */
        MarketQuoteResult: {
            /**
             * Adjustment State
             * @default not_applicable
             * @enum {string}
             */
            adjustment_state?: "adjusted" | "unadjusted" | "not_applicable" | "unknown";
            /** Change Percent */
            change_percent?: string | null;
            /** Currency */
            currency: string;
            /** Current Price */
            current_price: string;
            /** Delay Minutes */
            delay_minutes?: number | null;
            /** Exchange */
            exchange?: string | null;
            /** Fifty Two Week High */
            fifty_two_week_high?: string | null;
            /** Fifty Two Week Low */
            fifty_two_week_low?: string | null;
            /** Market */
            market: string;
            /** Market Cap */
            market_cap?: string | null;
            /**
             * Observed At
             * Format: date-time
             */
            observed_at?: string;
            /** Pe Ratio */
            pe_ratio?: string | null;
            /**
             * Price Type
             * @default unknown
             * @enum {string}
             */
            price_type?: "real_time" | "delayed" | "end_of_day" | "unknown" | "manual";
            /** Provider Name */
            provider_name: string;
            /** Provider Symbol */
            provider_symbol: string;
            /** Source Timestamp */
            source_timestamp?: string | null;
            /** Ticker */
            ticker: string;
            /** Volume */
            volume?: number | null;
            /** Warnings */
            warnings?: string[];
        };
        /** PeerDiscoveryRequest */
        PeerDiscoveryRequest: {
            /** Country */
            country?: string | null;
            /** Industry */
            industry?: string | null;
            /**
             * Limit
             * @default 50
             */
            limit?: number;
            /** Query */
            query?: string | null;
            /** Sector */
            sector?: string | null;
        };
        /** ReportObservation */
        ReportObservation: {
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Return Decimal */
            return_decimal: number;
        };
        /** ReportRequest */
        ReportRequest: {
            /** Benchmark */
            benchmark?: components["schemas"]["ReportObservation"][] | null;
            /**
             * Periods Per Year
             * @default 252
             */
            periods_per_year?: number;
            /** Returns */
            returns: components["schemas"]["ReportObservation"][];
            /**
             * Risk Free Rate
             * @default 0.04
             */
            risk_free_rate?: number;
            /** Source Label */
            source_label: string;
            /**
             * Title
             * @default Research return report
             */
            title?: string;
        };
        /** ResearchAsset */
        ResearchAsset: {
            /** Currency */
            currency: string;
            /** Key */
            key: string;
            /** Ticker */
            ticker: string;
        };
        /** ResearchCapabilities */
        ResearchCapabilities: {
            /** Adapters */
            adapters: components["schemas"]["AdapterCapability"][];
            /** Limits */
            limits: {
                [key: string]: number;
            };
            /** Warnings */
            warnings?: string[];
        };
        /** ResearchDataset */
        ResearchDataset: {
            /** Assets */
            assets: components["schemas"]["ResearchAsset"][];
            /** Base Currency */
            base_currency: string;
            /** Observations */
            observations: components["schemas"]["ReturnObservation"][];
            /**
             * Periods Per Year
             * @default 252
             */
            periods_per_year?: number;
            /**
             * Return Basis
             * @enum {string}
             */
            return_basis: "price_return" | "total_return";
            /** Source Label */
            source_label: string;
        };
        /** ResearchRunManifest */
        ResearchRunManifest: {
            /** Adapter */
            adapter: string;
            /** Adapter Version */
            adapter_version: string;
            /** Application Observed Cutoff */
            application_observed_cutoff?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Dependencies */
            dependencies: {
                [key: string]: string;
            };
            /**
             * Deterministic Seed
             * @default 0
             */
            deterministic_seed?: number;
            /** Input Sha256 */
            input_sha256: string;
            /**
             * Knowledge Policy
             * @enum {string}
             */
            knowledge_policy: "unverified_research" | "reference_snapshot";
            /** Output Sha256 */
            output_sha256: string;
            /** Public Information Cutoff */
            public_information_cutoff?: string | null;
            /**
             * Schema Version
             * @default research-lab/v1
             * @constant
             */
            schema_version?: "research-lab/v1";
            /**
             * Snapshot Created At
             * Format: date-time
             */
            snapshot_created_at: string;
            /**
             * Source Assertion
             * @enum {string}
             */
            source_assertion: "user_supplied_unverified" | "pinned_reference_snapshot";
            /** Valuation As Of */
            valuation_as_of?: string | null;
        };
        /** ResearchRunResult */
        ResearchRunResult: {
            /**
             * Kind
             * @enum {string}
             */
            kind: "allocation" | "simulation" | "report" | "peers";
            manifest: components["schemas"]["ResearchRunManifest"];
            /** Result */
            result: {
                [key: string]: unknown;
            };
            /** Run Id */
            run_id: number;
            /**
             * Status
             * @default complete
             * @constant
             */
            status?: "complete";
            /** Warnings */
            warnings?: string[];
        };
        /** ResearchRunSummary */
        ResearchRunSummary: {
            /** Adapter */
            adapter?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Input Sha256 */
            input_sha256?: string | null;
            /** Kind */
            kind: string;
            /** Run Id */
            run_id: number;
            /** Status */
            status: string;
        };
        /** ReturnObservation */
        ReturnObservation: {
            /**
             * End Date
             * Format: date
             */
            end_date: string;
            /** Returns */
            returns: {
                [key: string]: number;
            };
            /**
             * Start Date
             * Format: date
             */
            start_date: string;
        };
        /** SecFactsAdapterRequest */
        SecFactsAdapterRequest: {
            /** As Of */
            as_of?: string | null;
            /**
             * Max Years
             * @default 5
             */
            max_years?: number;
        };
        /** SecurityReferenceResult */
        SecurityReferenceResult: {
            /** Active */
            active?: boolean | null;
            /** Cik */
            cik?: string | null;
            /** Composite Figi */
            composite_figi?: string | null;
            /** Currency */
            currency: string;
            /** Exchange */
            exchange: string;
            /** Market */
            market: string;
            /** Name */
            name?: string | null;
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Provider */
            provider: string;
            /** Requested Date */
            requested_date?: string | null;
            /** Share Class Figi */
            share_class_figi?: string | null;
            /** Ticker */
            ticker: string;
            /** Warnings */
            warnings?: string[];
        };
        /** SimulationRequest */
        SimulationRequest: {
            dataset: components["schemas"]["ResearchDataset"];
            /**
             * Engine
             * @default native
             * @enum {string}
             */
            engine?: "native" | "bt";
            /** Initial Weights */
            initial_weights: {
                [key: string]: number;
            };
            /**
             * Rebalance
             * @default monthly
             * @enum {string}
             */
            rebalance?: "monthly" | "quarterly" | "yearly" | "each_period";
            /**
             * Strategy
             * @default buy_and_hold
             * @enum {string}
             */
            strategy?: "buy_and_hold" | "constant_weight";
            /**
             * Transaction Cost Bps
             * @default 0
             */
            transaction_cost_bps?: number;
            /**
             * Weight Decision Date
             * Format: date
             */
            weight_decision_date: string;
        };
        /** SourceAdapterCapability */
        SourceAdapterCapability: {
            /** Adapter */
            adapter: string;
            /** Available */
            available: boolean;
            /** Dependency Version */
            dependency_version?: string | null;
            /** Status */
            status: string;
            /** Warnings */
            warnings?: string[];
        };
        /** SourceAdapterResult */
        SourceAdapterResult: {
            /** Adapter */
            adapter: string;
            /** Candidate Ids */
            candidate_ids?: number[];
            /**
             * Created Count
             * @default 0
             */
            created_count?: number;
            /** Details */
            details?: {
                [key: string]: unknown;
            };
            /**
             * Duplicate Count
             * @default 0
             */
            duplicate_count?: number;
            /**
             * Fetched Count
             * @default 0
             */
            fetched_count?: number;
            /**
             * Observed At
             * Format: date-time
             */
            observed_at: string;
            /** Processing Run Id */
            processing_run_id?: number | null;
            /** Raw Document Ids */
            raw_document_ids?: number[];
            /**
             * Status
             * @default success
             * @enum {string}
             */
            status?: "success" | "partial" | "unavailable";
            /** Warnings */
            warnings?: string[];
        };
        /** TranscriptRequest */
        TranscriptRequest: {
            /** Exchange */
            exchange?: string | null;
            /** Fiscal Quarter */
            fiscal_quarter: number;
            /** Fiscal Year */
            fiscal_year: number;
            /**
             * Level
             * @default 1
             */
            level?: number;
            /**
             * Provider
             * @enum {string}
             */
            provider: "earningscall" | "fmp";
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    document_extract_api_companies__company_id__source_adapters_documents__document_id__extract_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                company_id: number;
                document_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DocumentExtractionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_SourceAdapterResult_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    india_filings_api_companies__company_id__source_adapters_india_filings_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                company_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["IndiaFilingsRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_SourceAdapterResult_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    sec_facts_api_companies__company_id__source_adapters_sec_facts_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                company_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SecFactsAdapterRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_SourceAdapterResult_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    transcript_api_companies__company_id__source_adapters_transcript_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                company_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TranscriptRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_SourceAdapterResult_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    adapter_actions_api_data_adapters__provider__corporate_actions_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                provider: "fmp" | "massive" | "nse_mcp";
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AdapterActionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_DataAdapterReceipt_AdapterActionsResult__"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    adapter_dated_quote_api_data_adapters__provider__dated_quote_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                provider: "fmp" | "massive" | "nse_mcp";
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AdapterDatedQuoteRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_DataAdapterReceipt_AdapterDatedQuoteResult__"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    adapter_history_api_data_adapters__provider__history_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                provider: "fmp" | "massive" | "nse_mcp";
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AdapterHistoryRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_DataAdapterReceipt_AdapterHistoryResult__"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    adapter_quote_api_data_adapters__provider__quote_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                provider: "fmp" | "massive" | "nse_mcp";
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarketDataRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_DataAdapterReceipt_MarketQuoteResult__"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    adapter_reference_api_data_adapters__provider__reference_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                provider: "fmp" | "massive" | "nse_mcp";
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarketDataRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_DataAdapterReceipt_SecurityReferenceResult__"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    adapter_calendar_api_data_adapters_calendars_schedule_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CalendarScheduleRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_DataAdapterReceipt_CalendarScheduleResult__"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    adapter_identity_api_data_adapters_identity_openfigi_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["IdentityMappingRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_DataAdapterReceipt_IdentityMappingResult__"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    allocation_api_research_lab_allocation_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AllocationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ResearchRunResult_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    research_capabilities_api_research_lab_capabilities_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ResearchCapabilities_"];
                };
            };
        };
    };
    peers_api_research_lab_peers_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PeerDiscoveryRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ResearchRunResult_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    report_api_research_lab_report_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReportRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ResearchRunResult_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    runs_api_research_lab_runs_get: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_list_ResearchRunSummary__"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    run_api_research_lab_runs__run_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ResearchRunResult_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_api_research_lab_runs__run_id__export_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    html_report_api_research_lab_runs__run_id__report_html_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    simulation_api_research_lab_simulation_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SimulationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_ResearchRunResult_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    source_capabilities_api_source_adapters_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_list_SourceAdapterCapability__"];
                };
            };
        };
    };
    fred_vintage_api_source_adapters_fred_vintage_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FredVintageRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiResponse_SourceAdapterResult_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
