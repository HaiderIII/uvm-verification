// ============================================================================
// AXI-Stream FIFO
// ============================================================================
// Simple synchronous FIFO with AXI-Stream interfaces
// - Slave interface (input) : s_axis_*
// - Master interface (output): m_axis_*
// ============================================================================

module axi_stream_fifo #(
    parameter DATA_WIDTH = 32,
    parameter FIFO_DEPTH = 8
) (
    input  logic                    clk,
    input  logic                    rst_n,

    // =========================================================================
    // Slave Interface (Input - receives data)
    // =========================================================================
    input  logic [DATA_WIDTH-1:0]   s_axis_tdata,
    input  logic                    s_axis_tvalid,
    output logic                    s_axis_tready,
    input  logic                    s_axis_tlast,

    // =========================================================================
    // Master Interface (Output - sends data)
    // =========================================================================
    output logic [DATA_WIDTH-1:0]   m_axis_tdata,
    output logic                    m_axis_tvalid,
    input  logic                    m_axis_tready,
    output logic                    m_axis_tlast
);

    // =========================================================================
    // Local parameters
    // =========================================================================
    localparam ADDR_WIDTH = $clog2(FIFO_DEPTH);

    // =========================================================================
    // FIFO storage - stores data + tlast bit
    // =========================================================================
    logic [DATA_WIDTH:0] fifo_mem [0:FIFO_DEPTH-1];  // +1 for TLAST

    // =========================================================================
    // Pointers and counters
    // =========================================================================
    logic [ADDR_WIDTH-1:0] wr_ptr;
    logic [ADDR_WIDTH-1:0] rd_ptr;
    logic [ADDR_WIDTH:0]   count;  // One extra bit to distinguish full/empty

    // =========================================================================
    // Status signals
    // =========================================================================
    logic full;
    logic empty;

    assign full  = (count == FIFO_DEPTH);
    assign empty = (count == 0);

    // =========================================================================
    // AXI-Stream handshake
    // =========================================================================
    // Ready to receive if not full
    assign s_axis_tready = ~full;

    // Valid output if not empty
    assign m_axis_tvalid = ~empty;

    // Output data from FIFO head
    assign m_axis_tdata = fifo_mem[rd_ptr][DATA_WIDTH-1:0];
    assign m_axis_tlast = fifo_mem[rd_ptr][DATA_WIDTH];

    // =========================================================================
    // Write logic (Slave side)
    // =========================================================================
    wire write_en = s_axis_tvalid & s_axis_tready;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= '0;
        end else if (write_en) begin
            fifo_mem[wr_ptr] <= {s_axis_tlast, s_axis_tdata};
            wr_ptr <= wr_ptr + 1'b1;
        end
    end

    // =========================================================================
    // Read logic (Master side)
    // =========================================================================
    wire read_en = m_axis_tvalid & m_axis_tready;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr <= '0;
        end else if (read_en) begin
            rd_ptr <= rd_ptr + 1'b1;
        end
    end

    // =========================================================================
    // Count logic
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= '0;
        end else begin
            case ({write_en, read_en})
                2'b10:   count <= count + 1'b1;  // Write only
                2'b01:   count <= count - 1'b1;  // Read only
                default: count <= count;          // Both or neither
            endcase
        end
    end

endmodule
