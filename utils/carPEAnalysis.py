import numpy as np
import matplotlib.pyplot as plt
import torch
import pickle
from gym_reachability import gym_reachability  # Custom Gym env.
import gym

from KC_DQN.config import dqnConfig
from KC_DQN.DDQNPursuitEvasion import DDQNPursuitEvasion


#== PLOTTING ==
tiffany = '#0abab5'

def plotTrajStep(state, env, agent, c=[tiffany, 'y'], lw=2, nx=101, ny=101, toEnd=False, T=100):
    """
    plotTrajStep [summary]

    Args:
        state ([type]): [description]
        env ([type]): [description]
        agent ([type]): [description]
        c (list, optional): [description]. Defaults to [tiffany, 'y'].
        lw (int, optional): [description]. Defaults to 2.
        nx (int, optional): [description]. Defaults to 101.
        ny (int, optional): [description]. Defaults to 101.
        toEnd (bool, optional): [description]. Defaults to False.
        T (int, optional): [description]. Defaults to 100.

    Returns:
        [type]: [description]
    
    Example:
        state = np.array([-.9, 0., 0., -.5, -.3, .75*np.pi])
        valueList, lxList, gxList = plotTrajStep(state, env, agent)
    """    
    trajEvader, trajPursuer, result, minV, info = env.simulate_one_trajectory(agent.Q_network, T=T, state=state, toEnd=toEnd)
    valueList = info['valueList']
    gxList = info['gxList']
    lxList = info['lxList']
    print('trajectory length is {:d}'.format(trajEvader.shape[0]))
    
    #== PLOT ==
    trajEvaderX = trajEvader[:,0]
    trajEvaderY = trajEvader[:,1]
    trajPursuerX = trajPursuer[:,0]
    trajPursuerY = trajPursuer[:,1]
    numCol = 5
    numRow = int(np.ceil(trajEvader.shape[0]/numCol))
    numAx = int(numRow*numCol)
    fig, axes = plt.subplots(numRow, numCol, figsize=(4*numCol, 4*numRow))

    for i in range(trajEvader.shape[0]):
        print("{:d}/{:d}".format(i+1, numAx), end='\r')
        rowIdx = int(i/numCol)
        colIdx = i % numCol
        if numRow > 1:
            ax = axes[rowIdx][colIdx]
        else:
            ax = axes[colIdx]
        xPursuer = trajPursuer[i,0]
        yPursuer = trajPursuer[i,1]
        thetaPursuer =trajPursuer[i,2]
        theta = trajEvader[i,2]

        cbarPlot = (i % numCol) == (numCol-1)
        ax.scatter(trajEvaderX[i], trajEvaderY[i], s=48, c=c[0], zorder=3)
        ax.plot(trajEvaderX[i:], trajEvaderY[i:], color=c[0],  linewidth=lw, zorder=2)
        ax.scatter(trajPursuerX[i], trajPursuerY[i], s=48, c=c[1], zorder=3)
        ax.plot(trajPursuerX[i:], trajPursuerY[i:], color=c[1],  linewidth=lw, zorder=2)

        env.plot_formatting(ax=ax)
        env.plot_target_failure_set(ax=ax, xPursuer=xPursuer, yPursuer=yPursuer)
        env.plot_v_values(  agent.Q_network, ax=ax, fig=fig, cbarPlot=cbarPlot,
                            theta=theta, xPursuer=xPursuer, yPursuer=yPursuer, thetaPursuer=thetaPursuer,
                            cmap='seismic', vmin=-.5, vmax=.5, nx=nx, ny=ny)
        ax.set_title(r'$v={:.3f}$'.format(valueList[i]), fontsize=16)
    return valueList, lxList, gxList


def plotCM(fig, ax, cm, target_names=['0', '1'], labels=['', ''],
    fontsize=20, thresh=.5, cmap='viridis', cbarPlot=False):

    im = ax.imshow(cm, interpolation='none', cmap=cmap, vmin=0, vmax=1.)
    if cbarPlot:
        cbar = fig.colorbar(im, ax=ax, pad=0.01, fraction=0.05, shrink=.75,
            ticks=[0, .5, 1.])
        cbar.ax.set_yticklabels(labels=[0, .5, 1.], fontsize=fontsize-4)

    if target_names is not None:
        tick_marks = np.arange(len(target_names))
        ax.set_xticks(tick_marks)
        ax.set_yticks(tick_marks)
        ax.set_xticklabels(target_names, rotation=0,  fontsize=fontsize-4)
        ax.set_yticklabels(target_names, rotation=90, fontsize=fontsize-4)

    it = np.nditer(cm, flags=['multi_index'])
    while not it.finished:
        i, j = it.multi_index

        ax.text(j, i, "{:0.3f}".format(cm[i, j]),
                    horizontalalignment="center",
                    color="k" if cm[i, j] > thresh else "w",
                    fontsize=fontsize)
        it.iternext()
    ax.set_xlabel(labels[0], fontsize=fontsize)
    ax.set_ylabel(labels[1], fontsize=fontsize)


def plotAndObtainValueDictIdx(env, dictList, testIdxList, indices,
    instantList=None, showCapture=False,
    maxCol=10, maxRow=2, width=2, height=2,
    lw=1.5, s=48):

    numCol = min(len(indices), maxCol)
    numRow = min(int(np.ceil(len(indices)/numCol)), maxRow)
    numAx = int(numRow*numCol)

    figWidth = width*numCol
    figHeight = height*numRow
    fig, axes = plt.subplots(numRow, numCol, figsize=(figWidth, figHeight))
    valueList = np.empty(shape=(len(indices),), dtype=float)

    for i, pick in enumerate(indices):
        print("{:d}/{:d}".format(i+1, len(indices)), end='\r')
        if instantList is not None:
            instant = instantList[i]
        dictTmp = dictList[pick]
        testIdx = testIdxList[pick]
        maxminV = dictTmp['maxminV']
        valueList[i] = maxminV
        
        #= PLOT =
        if i < numAx:
            rowIdx = int(i/numCol)
            colIdx = i % numCol
            if numRow > 1:
                ax = axes[rowIdx][colIdx]
            elif numCol > 1:
                ax = axes[colIdx]
            else:
                ax = axes
            trajEvaderTmp = dictTmp['trajEvader']
            trajPursuerTmp = dictTmp['trajPursuer']

            traj_x = trajEvaderTmp[:,0]
            traj_y = trajEvaderTmp[:,1]
            ax.scatter(traj_x[0], traj_y[0], s=s, c='#0abab5')
            ax.plot(traj_x, traj_y, color='#0abab5',  linewidth=lw)
            if instantList is not None:
                markerColor = 'b' if showCapture else 'r'
                ax.scatter(traj_x[instant], traj_y[instant], marker='x', s=s,
                    c=markerColor, zorder=4)

            traj_x = trajPursuerTmp[:,0]
            traj_y = trajPursuerTmp[:,1]
            ax.scatter(traj_x[0], traj_y[0], s=s, c='y')
            ax.plot(traj_x, traj_y, color='y',  linewidth=lw)
            if instantList is not None:
                if showCapture:
                    env.plot_target_failure_set(ax=ax, xPursuer=traj_x[instant],
                        yPursuer=traj_y[instant], lw=lw)
                    ax.scatter(traj_x[instant], traj_y[instant],
                        marker='x', s=s, c='b', zorder=4)
                else:
                    env.plot_target_failure_set(ax, showCapture=False, lw=lw)
            else:
                env.plot_target_failure_set(ax, showCapture=False, lw=lw)
            env.plot_formatting(ax=ax)
            ax.set_title('[{:d}]: {:.2f}'.format(testIdx, maxminV), fontsize=14)
            ax.set_xticklabels([])
            ax.set_yticklabels([])
    plt.tight_layout()
    plt.show()

    return valueList


#== DATA ANALYSIS ==
def generateCM(labelValue, predictValue):
    FPMtx = np.logical_and((labelValue <= 0), (predictValue > 0))
    FPIndices = np.argwhere(FPMtx)
    FPNum = np.sum(FPMtx)

    FNMtx = np.logical_and((labelValue > 0), (predictValue <= 0))
    FNIndices = np.argwhere(FNMtx)
    FNNum = np.sum(FNMtx)

    TPMtx = np.logical_and((labelValue > 0), (predictValue > 0))
    TPIndices = np.argwhere(TPMtx)
    TPNum = np.sum(TPMtx)

    TNMtx = np.logical_and((labelValue <= 0), (predictValue <= 0))
    TNIndices = np.argwhere(TNMtx)
    TNNum = np.sum(TNMtx)

    accuracy = (TPNum+TNNum)/(TPNum+TNNum+FPNum+FNNum)
    FPrate = FPNum / (FPNum+TNNum)
    FNrate = FNNum / (TPNum+FNNum)
    TNrate = TNNum / (FPNum+TNNum)
    TPrate = TPNum / (TPNum+FNNum)

    print('TP: {:.0f}, FP: {:.0f}, FN: {:.0f}, TN: {:.0f}'.format(
        TPNum, FPNum, FNNum, TNNum))
    cm = np.array([ [TPrate, FNrate],
                    [FPrate, TNrate] ])

    return cm, accuracy, TPIndices, FNIndices, FPIndices, TNIndices


#== GENERATE TRAJECTORIES ==
def pursuerResponse(env, agent, statePursuer, trajEvader):
    trajPursuer = []
    result = 0 # not finished

    valueList=[]
    gxList=[]
    lxList=[]
    for t in range(trajEvader.shape[0]):
        stateEvader = trajEvader[t]
        trajPursuer.append(statePursuer)
        state = np.concatenate((stateEvader, statePursuer), axis=0)
        donePursuer = not env.pursuer.check_within_bounds(statePursuer)

        g_x = env.safety_margin(state)
        l_x = env.target_margin(state)

        #= Rollout Record
        if t == 0:
            maxG = g_x
            current = max(l_x, maxG)
            minV = current
        else:
            maxG = max(maxG, g_x)
            current = max(l_x, maxG)
            minV = min(current, minV)

        valueList.append(minV)
        gxList.append(g_x)
        lxList.append(l_x)

        #= Dynamics
        stateTensor = torch.FloatTensor(state).to(env.device)
        with torch.no_grad():
            state_action_values = agent.Q_network(stateTensor)
        Q_mtx = state_action_values.reshape(env.numActionList[0], env.numActionList[1])
        pursuerValues, colIndices = Q_mtx.max(dim=1)
        minmaxValue, rowIdx = pursuerValues.min(dim=0)
        colIdx = colIndices[rowIdx]

        # If cars are within the boundary, we update their states according to the controls
        if not donePursuer:
            uPursuer = env.pursuer.discrete_controls[colIdx]
            statePursuer = env.pursuer.integrate_forward(statePursuer, uPursuer)

    trajPursuer = np.array(trajPursuer)
    info = {'valueList':valueList, 'gxList':gxList, 'lxList':lxList}
    return trajPursuer, result, minV, info


def exhaustiveDefenderSearch(env, agent, state, actionSeq, maxLength=40):
    numChunk = actionSeq.shape[0]
    chunkLength = int(np.ceil(maxLength/numChunk))
    stateEvader  = state[:3]
    statePursuer = state[3:]
    trajPursuer = [statePursuer]
    trajEvader = [stateEvader]
    valueList = []
    gxList = []
    lxList = []
    pursuerActionSeqIdx = 0

    for t in range(maxLength):
        state = np.concatenate((stateEvader, statePursuer), axis=0)
        doneEvader = not env.evader.check_within_bounds(stateEvader)
        donePursuer = not env.pursuer.check_within_bounds(statePursuer)

        g_x = env.safety_margin(state)
        l_x = env.target_margin(state)

        #= Rollout Record
        if t == 0:
            maxG = g_x
            current = max(l_x, maxG)
            minV = current
        else:
            maxG = max(maxG, g_x)
            current = max(l_x, maxG)
            minV = min(current, minV)

        valueList.append(minV)
        gxList.append(g_x)
        lxList.append(l_x)

        #= Dynamics
        stateTensor = torch.FloatTensor(state).to(env.device)
        with torch.no_grad():
            state_action_values = agent.Q_network(stateTensor)
        Q_mtx = state_action_values.reshape(env.numActionList[0], env.numActionList[1])
        pursuerValues, colIndices = Q_mtx.max(dim=1)
        minmaxValue, rowIdx = pursuerValues.min(dim=0)
        colIdx = colIndices[rowIdx]

        # If cars are within the boundary, we update their states according to the controls
        uEvader = env.evader.discrete_controls[rowIdx]
        stateEvader = env.evader.integrate_forward(stateEvader, uEvader)
        actionIdx = actionSeq[pursuerActionSeqIdx]
        uPursuer = env.pursuer.discrete_controls[actionIdx]
        statePursuer = env.pursuer.integrate_forward(statePursuer, uPursuer)

        trajPursuer.append(statePursuer)
        trajEvader.append(stateEvader)
        if (t+1) % chunkLength == 0:
            pursuerActionSeqIdx += 1

    trajEvader = np.array(trajEvader)
    trajPursuer = np.array(trajPursuer)
    info = {'valueList':valueList, 'gxList':gxList, 'lxList':lxList}
    return trajEvader, trajPursuer, minV, info


#! exhaustiveAttackerSearch
def exhaustiveAttackerSearch(env, agent, state, actionSeq, maxLength=40):
    numChunk = actionSeq.shape[0]
    chunkLength = int(np.ceil(maxLength/numChunk))
    stateEvader  = state[:3]
    statePursuer = state[3:]
    trajPursuer = [statePursuer]
    trajEvader = [stateEvader]
    valueList = []
    gxList = []
    lxList = []
    pursuerActionSeqIdx = 0

    for t in range(maxLength):
        state = np.concatenate((stateEvader, statePursuer), axis=0)
        doneEvader = not env.evader.check_within_bounds(stateEvader)
        donePursuer = not env.pursuer.check_within_bounds(statePursuer)

        g_x = env.safety_margin(state)
        l_x = env.target_margin(state)

        #= Rollout Record
        if t == 0:
            maxG = g_x
            current = max(l_x, maxG)
            minV = current
        else:
            maxG = max(maxG, g_x)
            current = max(l_x, maxG)
            minV = min(current, minV)

        valueList.append(minV)
        gxList.append(g_x)
        lxList.append(l_x)

        #= Dynamics
        stateTensor = torch.FloatTensor(state).to(env.device)
        with torch.no_grad():
            state_action_values = agent.Q_network(stateTensor)
        Q_mtx = state_action_values.reshape(env.numActionList[0], env.numActionList[1])
        pursuerValues, colIndices = Q_mtx.max(dim=1)
        minmaxValue, rowIdx = pursuerValues.min(dim=0)
        colIdx = colIndices[rowIdx]

        # If cars are within the boundary, we update their states according to the controls
        if not doneEvader:
            uEvader = env.evader.discrete_controls[rowIdx]
            stateEvader = env.evader.integrate_forward(stateEvader, uEvader)
        if not donePursuer:
            actionIdx = actionSeq[pursuerActionSeqIdx]
            uPursuer = env.pursuer.discrete_controls[actionIdx]
            statePursuer = env.pursuer.integrate_forward(statePursuer, uPursuer)

        trajPursuer.append(statePursuer)
        trajEvader.append(stateEvader)
        if (t+1) % chunkLength == 0:
            pursuerActionSeqIdx += 1

    trajEvader = np.array(trajEvader)
    trajPursuer = np.array(trajPursuer)
    info = {'valueList':valueList, 'gxList':gxList, 'lxList':lxList}
    return trajEvader, trajPursuer, minV, info


def validateEvaderPolicy(env, agent, state, maxLength=40, numChunk=10):
    actionSet= np.empty(shape=(env.numActionList[1], numChunk), dtype=int)
    for i in range(numChunk):
        actionSet[:, i] = np.arange(env.numActionList[1])

    shapeTmp = np.ones(numChunk, dtype=int)*env.numActionList[1]
    rolloutResult = np.empty(shape=shapeTmp, dtype=int)
    it = np.nditer(rolloutResult, flags=['multi_index'])
    responseDict={'state':state, 'maxLength':maxLength, 
        'numChunk':numChunk}
    flag = True
    while not it.finished:
        idx = it.multi_index
        actionSeq = actionSet[idx, np.arange(numChunk)]
        print(actionSeq, end='\r')
        trajEvader, trajPursuer, minV, _ = exhaustiveDefenderSearch(
            env, agent, state, actionSeq, maxLength)
        info = {'trajEvader':trajEvader, 'trajPursuer':trajPursuer, 'minV':minV}
        responseDict[idx] = info
        it.iternext()
        if flag:
            maxminV = minV
            maxminIdx = idx
            flag = False
        elif minV > maxminV:
            maxminV = minV
            maxminIdx = idx
    responseDict['maxminV'] = maxminV
    responseDict['maxminIdx'] = maxminIdx
    return responseDict


def checkCapture(env, trajEvader, trajPursuer):
    numStep = trajEvader.shape[0]
    captureFlag = False
    captureInstant = None
    for t in range(numStep):
        posEvader = trajEvader[t, :2]
        posPursuer = trajPursuer[t, :2]
        dist_evader_pursuer = np.linalg.norm(posEvader-posPursuer, ord=2)
        capture_g_x = env.capture_range - dist_evader_pursuer
        # however, the value can be lower than this captureValue because we care
        # about the minimum value along the trajectory. 
        if capture_g_x > 0:
            if not captureFlag:
                captureInstant = t
                captureValue = capture_g_x
                captureFlag = True
            elif capture_g_x > captureValue:
                captureInstant = t
                captureValue = capture_g_x
    return captureFlag, captureInstant


def checkCrossConstraint(env, trajEvader, trajPursuer):
    numStep = trajEvader.shape[0]
    crossConstraintFlag = False
    crossConstraintInstant = None
    for t in range(numStep):
        posEvader = trajEvader[t, :2]
        evader_g_x = env.evader.safety_margin(posEvader)
        if not crossConstraintFlag and evader_g_x > 0:
            crossConstraintInstant = t
            crossConstraintFlag = True
    return crossConstraintFlag, crossConstraintInstant


def analyzeValidationResult(validationFile, env):
    print('Load from {:s} ...'.format(validationFile))
    valDict = np.load(validationFile, allow_pickle='TRUE').item()
    print(valDict.keys())

    dictList = valDict['dictList']
    testIdxList = valDict['testIdxList']
    failureList = []
    successList = []
    for i, dictTmp in enumerate(dictList):
        maxminV = dictTmp['maxminV']
        if maxminV > 0:
            failureList.append(i)
        else:
            successList.append(i)
    print('Failure Ratio: {:d} / {:d} = {:.2%}.'.format(
        len(failureList), len(dictList), len(failureList)/len(dictList) ))

    #== ANALYZE FAILED STATES ==
    captureList = []
    captureInstantList = []
    crossConstraintList = []
    crossConstraintInstantList = []
    unfinishedList = []
    for i, pick in enumerate(failureList):
        print("{:d}/{:d}".format(i+1, len(failureList)), end='\r')
        dictTmp = dictList[pick]
        trajEvaderTmp = dictTmp['trajEvader']
        trajPursuerTmp = dictTmp['trajPursuer']
        captureFlag, captureInstant = \
            checkCapture(env, trajEvaderTmp, trajPursuerTmp)
        crossConstraintFlag, crossConstraintInstant = \
            checkCrossConstraint(env, trajEvaderTmp, trajPursuerTmp)
        if captureFlag:
            if crossConstraintFlag:
                if captureInstant < crossConstraintInstant:
                    captureList.append(pick)
                    captureInstantList.append(captureInstant)
                else:
                    crossConstraintList.append(pick)
                    crossConstraintInstantList.append(crossConstraintInstant)
            else:
                captureList.append(pick)
                captureInstantList.append(captureInstant)
        elif crossConstraintFlag:
            crossConstraintList.append(pick)
            crossConstraintInstantList.append(crossConstraintInstant)
        else:
            unfinishedList.append(pick)
    print('{:d} captured, {:d} crosses, {:d} unfinished, {:d} succeeds'.format(
        len(captureList), len(crossConstraintList), len(unfinishedList),
        len(successList) ))
    return valDict, successList, failureList, captureList, captureInstantList,\
            crossConstraintList, crossConstraintInstantList, unfinishedList


def colUnfinishedSamples(unfinishedList, valDict, valSamplesDict):
    """
    colUnfinishedSamples [summary]

    Args:
        unfinishedList (list): the test indices of unfinished samples.
        valDict (dict): includes
            'dictList'
            'stateIdxList': the index of states by `genEstSamples.py`
            'testIdxList': the index of states by `genValSamples.py`
        valSamplesDict (dict): includes
            'idxList': the index of states by `genEstSamples.py`
            'rollvalList': the rollout values of states by `genEstSamples.py`
            'ddqnList': the DDQN values of states by `genEstSamples.py`
    """    
    #== add to valSamplesTN ==
    unfinishedStateIdxList = []
    unfinishedStateList = np.empty(shape=(len(unfinishedList), 6), dtype=float)
    newRolloutValueList = np.empty(shape=(len(unfinishedList),), dtype=float)
    newDdqnValueList    = np.empty(shape=(len(unfinishedList),), dtype=float)
    unfinishedValueList = np.empty(shape=(len(unfinishedList),), dtype=float)
    
    dictList = valDict['dictList']
    stateIdxList = valDict['stateIdxList']
    testIdxList = valDict['testIdxList']

    for i, pick in enumerate(unfinishedList):
        print("{:d}/{:d}".format(i+1, len(unfinishedList)), end='\r')

        testIdx = testIdxList[pick]
        dictTmp = dictList[pick]
        stateIdx = stateIdxList[pick]
        maxminV = dictTmp['maxminV']
        maxminIdx = dictTmp['maxminIdx']
        trajEvaderTmp = dictTmp['trajEvader']
        trajPursuerTmp = dictTmp['trajPursuer']

        state = np.empty(shape=(6,), dtype=float)
        state[:3] = trajEvaderTmp[-1, :]
        state[3:] = trajPursuerTmp[-1, :]

        rolloutValue = valSamplesDict['rollvalList'][testIdx]
        ddqnValue    = valSamplesDict['ddqnList'][testIdx]

        unfinishedValueList[i] = maxminV
        unfinishedStateIdxList.append(stateIdx)
        unfinishedStateList[i, :] = state
        newRolloutValueList[i] = rolloutValue
        newDdqnValueList[i] = ddqnValue

    #== RECORD ==
    finalDict = {}
    finalDict['states'] = unfinishedStateList
    finalDict['idxList'] = unfinishedStateIdxList
    finalDict['ddqnList'] = newDdqnValueList
    finalDict['rollvalList'] = newRolloutValueList
    finalDict['unfinishedValueList'] = unfinishedValueList
    finalDict['pickList'] = unfinishedList # indices of validation samples

    return finalDict


#== LOADING ==
def loadEnv(args, verbose=True):
    env_name = "dubins_car_pe-v0"
    if args.forceCPU:
        device = torch.device("cpu")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    env = gym.make(env_name, device=device, mode='RA', doneType='toEnd')
    env.set_considerPursuerFailure(args.cpf)
    if verbose:
        print("\n== Environment Information ==")
        env.report()
        print()
    return env


def loadAgent(args, device, stateNum, actionNum, numActionList,
    verbose=True):
    if verbose:
        print("\n== Agent Information ==")
    configFile = '{:s}/CONFIG.pkl'.format(args.modelFolder)
    with open(configFile, 'rb') as handle:
        tmpConfig = pickle.load(handle)
    CONFIG = dqnConfig()
    for key, value in tmpConfig.__dict__.items():
        CONFIG.__dict__[key] = tmpConfig.__dict__[key]
    CONFIG.DEVICE = device
    CONFIG.SEED = 0

    dimList = [stateNum] + CONFIG.ARCHITECTURE + [actionNum]
    agent = DDQNPursuitEvasion(CONFIG, numActionList, dimList,
        CONFIG.ACTIVATION, verbose=verbose)
    modelFile = '{:s}/model-{:d}.pth'.format(args.modelFolder+'/model', 4000000)
    agent.restore(modelFile, verbose)

    if verbose:
        print(vars(CONFIG))
        print('agent\'s device:', agent.device)

    return agent