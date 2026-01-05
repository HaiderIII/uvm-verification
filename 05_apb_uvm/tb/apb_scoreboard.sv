// ============================================================================
// APB Scoreboard
// ============================================================================
// Vérifie les transactions APB avec un modèle de référence
// Reçoit les transactions du monitor via analysis_export
// ============================================================================

class apb_scoreboard extends uvm_scoreboard;

    // =========================================================================
    // Enregistrement UVM
    // =========================================================================
    `uvm_component_utils(apb_scoreboard)

    // =========================================================================
    // Analysis Export - Pour recevoir les transactions du monitor
    // =========================================================================
    uvm_analysis_imp #(apb_seq_item, apb_scoreboard) analysis_export;

    // =========================================================================
    // Modèle de référence - Copie des 4 registres
    // =========================================================================
    bit [31:0] ref_regs [0:3];

    // =========================================================================
    // Compteurs
    // =========================================================================
    int num_writes;
    int num_reads;
    int num_errors;

    // =========================================================================
    // Constructeur
    // =========================================================================
    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    // =========================================================================
    // Build Phase
    // =========================================================================
    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        // Créer l'analysis export
        analysis_export = new("analysis_export", this);

        // Initialiser le modèle de référence
        foreach (ref_regs[i]) ref_regs[i] = '0;

        // Initialiser les compteurs
        num_writes = 0;
        num_reads  = 0;
        num_errors = 0;
    endfunction

    // =========================================================================
    // Write Function - Appelée par le monitor via analysis_port
    // =========================================================================
    // Cette fonction est la callback du analysis_imp
    virtual function void write(apb_seq_item txn);
        int reg_idx;

        // Calculer l'index du registre
        reg_idx = txn.addr[3:2];

        if (txn.write) begin
            // -----------------------------------------------------------------
            // TODO 1: Vérification ÉCRITURE
            // -----------------------------------------------------------------
            // Mettre à jour le modèle de référence
            ref_regs[reg_idx] = txn.wdata;
            num_writes++;

            `uvm_info(get_name(),
                $sformatf("WRITE: reg[%0d] = 0x%08h", reg_idx, txn.wdata),
                UVM_MEDIUM)
        end
        else begin
            // -----------------------------------------------------------------
            // TODO 2: Vérification LECTURE
            // -----------------------------------------------------------------
            // Comparer la donnée lue avec le modèle de référence
            num_reads++;

            if (txn.rdata !== ref_regs[reg_idx]) begin
                `uvm_error(get_name(),
                    $sformatf("READ MISMATCH: reg[%0d] expected=0x%08h, got=0x%08h",
                              reg_idx, ref_regs[reg_idx], txn.rdata))
                num_errors++;
            end
            else begin
                `uvm_info(get_name(),
                    $sformatf("READ OK: reg[%0d] = 0x%08h", reg_idx, txn.rdata),
                    UVM_MEDIUM)
            end
        end
    endfunction

    // =========================================================================
    // Report Phase - Afficher le résumé
    // =========================================================================
    virtual function void report_phase(uvm_phase phase);
        super.report_phase(phase);

        `uvm_info(get_name(), "========================================", UVM_LOW)
        `uvm_info(get_name(), "         SCOREBOARD SUMMARY             ", UVM_LOW)
        `uvm_info(get_name(), "========================================", UVM_LOW)
        `uvm_info(get_name(), $sformatf("  Writes:  %0d", num_writes), UVM_LOW)
        `uvm_info(get_name(), $sformatf("  Reads:   %0d", num_reads), UVM_LOW)
        `uvm_info(get_name(), $sformatf("  Errors:  %0d", num_errors), UVM_LOW)
        `uvm_info(get_name(), "========================================", UVM_LOW)

        if (num_errors == 0) begin
            `uvm_info(get_name(), "*** TEST PASSED ***", UVM_LOW)
        end
        else begin
            `uvm_error(get_name(), "*** TEST FAILED ***")
        end
    endfunction

endclass
