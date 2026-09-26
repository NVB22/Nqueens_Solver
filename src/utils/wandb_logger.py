import wandb
import pandas as pd
import os

def init_wandb(project_name="NQueens-Optimization", run_name="Functional-Pipeline"):
    """Khởi tạo phiên làm việc W&B và định nghĩa các trục đồ thị"""
    wandb.init(project=project_name, name=run_name)
    
    # Ép W&B sử dụng N làm trục X mặc định thay vì Step
    wandb.define_metric("N")
    wandb.define_metric("Time", step_metric="N")
    wandb.define_metric("Variables", step_metric="N")
    wandb.define_metric("Clauses", step_metric="N")
    wandb.define_metric("RAM_MB", step_metric="N")

def log_result(data: dict, csv_path="experiment_results.csv"):
    """Log dữ liệu lên đám mây và đồng thời ghi nối vào file CSV cục bộ"""
    wandb.log(data)
    
    df = pd.DataFrame([data])
    if not os.path.isfile(csv_path):
        df.to_csv(csv_path, index=False)
    else:
        df.to_csv(csv_path, mode='a', header=False, index=False)
        
def finish_wandb():
    wandb.finish()