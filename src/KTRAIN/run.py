import time
import glob
import pandas as pd
import os
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, matthews_corrcoef

import ktrain
from ktrain import vision as vis
from tensorflow.keras.callbacks import CSVLogger

from src.utils.handle_hist import load_dataset
from src.utils.create_resources_folder import resources
from src.utils.handle_results import save_results
from src.utils.handle_ktrain_folders import delete_tmp_and_checkpoint

def main(
        path_metadata: str,
        path_dataset: str,
        steps: int,
        target_size=(255, 255)):
        
        """
        :param path_metadata:
        :param path_dataset:
        :param steps:
        :param target_size:
        :return:
        """
       
        resources()

        print('Time --> Start')
        start_time = time.time()

        # Handling files and folders continuosly created by Ktrain
        directory = "./"
        delete_tmp_and_checkpoint(directory)

        print('Loading Data')
        dataset = load_dataset(path_metadata, path_dataset)
        n_data = dataset.n_data
        new_path = dataset.to_folders()

        (trn, val, preproc) = vis.images_from_folder(
            datadir=new_path,
            data_aug=vis.get_data_aug(horizontal_flip=True),
            train_test_names=['train', 'valid'],
            #target_size=(224,224),
            color_mode='rgb'
            )

        print('Loading Pre-Trained Model')
        model = vis.image_classifier(
                'pretrained_mobilenet', # pretrained_resnet50 / pretrained_mobilenet
                trn,
                val,
                freeze_layers=15)

        print('Fitting Model')
        learner = ktrain.get_learner(
                model=model,
                train_data=trn,
                val_data=val,
                workers=5,
                use_multiprocessing=False,
                batch_size=64
                )

        # Find appropriate lr
        learner.lr_find(max_epochs=5, verbose=1) #5
        # learner.lr_plot(suggest=True)

        # Add CSVLogger to log to save the history in a csv file
        csv_file = CSVLogger('resources/ktrain_ghost.csv')
        
        print('Fitting Model')
        learner.autofit(2e-5, callbacks=[csv_file])
        #learner.fit_onecycle(2e-5, 2, callbacks=[csv_file])

        csv_path = 'resources/ktrain_ghost.csv'
        df = pd.read_csv(csv_path)

        histories = {}  

        for column in df.columns:
            histories[column] = [df[column].tolist()]

        # Ktrain provides learn.evaluate() (likely not functioning since the scores do 
        # not match the predictions info, which is within the same range of learning curves info)

        print('Predictions')
        predictor = ktrain.get_predictor(learner.model, preproc)

        directory_path = new_path + '/test'
        y_true = []
        y_pred = []
        y_prob = []

        for subfolder in os.listdir(directory_path): # within the classes
            class_label = int(subfolder)
            folder_path = os.path.join(directory_path, subfolder)

            for image_path in glob.glob(os.path.join(folder_path, '*.png')):
                # Predicted label
                prediction = predictor.predict_filename(image_path)
                predicted_class = int(prediction[0])
                y_pred.append(predicted_class)

                # Probability of predicted label
                probability_class = prediction[1]
                y_prob.append(probability_class)

                # Actual label
                y_true.append(class_label)
        
        # Accuracy, Precision, Recall, F1-Score, AUC, MCC
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred)
        rec = recall_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)
        auc = roc_auc_score(y_true, y_prob)
        mcc = matthews_corrcoef(y_true, y_pred)

        scores={}
        results=[acc, prec, rec, f1, auc, mcc]
        metric_names=['accuracy', 'precision', 'recall', 'f1', 'auc', 'mcc']
        for i in range(len(results)):
            rounded_values = round(results[i], 4)
            scores[metric_names[i]] = rounded_values

        print('Time --> Stop')
        elapsed_time = time.time() - start_time
        scores['time']=elapsed_time
        print('Time:', elapsed_time)

        print('Saving Results...')

        df_1 = pd.DataFrame(histories)
        df_2 = pd.DataFrame(scores, index=[0])
        df_3 = pd.DataFrame(predictions_and_more)
        all_results = pd.concat([df_1, df_2, df_3], axis=1)

        all_results.to_csv('resources/ktrain_results.csv', mode='a', index=False)
        print('Results Ready!')

        # Handling files and folders continuosly created
        directory = "./"
        delete_tmp_and_checkpoint(directory)

